from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging
from sqlalchemy import and_

from src.database import get_db, User, Meeting, UserRole, UserStatus, MeetingStatus, Reminder
from src.services.meeting_service import MeetingService
from src.services.owner_service import OwnerService
from src.services.google_calendar import GoogleCalendarService
from src.services.reminder_service import ReminderService
from src.config import settings
from src.utils.decorators import require_registration

logger = logging.getLogger(__name__)

@require_registration
async def show_available_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available meeting slots when both owners are free."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if user.role != UserRole.MANAGER:
            await update.message.reply_text(
                "❌ Данная функция доступна только руководителям отделов."
            )
            return
            
        if user.status != UserStatus.ACTIVE:
            status_text = {
                UserStatus.VACATION: "В отпуске",
                UserStatus.SICK_LEAVE: "На больничном",
                UserStatus.BUSINESS_TRIP: "В командировке"
            }.get(user.status, "неактивном статусе")
            
            await update.message.reply_text(
                f"❌ Вы находитесь в статусе: {status_text}.\n\n"
                f"Для назначения встреч сначала вернитесь в активный статус: /active"
            )
            return
    
    try:
        with get_db() as db:
            meeting_service = MeetingService(db)
            
            # Get available slots when both owners are free
            available_slots = meeting_service.get_available_slots(days_ahead=14)
            
            if not available_slots:
                await update.message.reply_text(
                    "❌ К сожалению, на ближайшие 2 недели нет свободных слотов.\n\n"
                    "🕐 Слоты доступны только когда свободны оба владельца бизнеса.\n"
                    "📞 Обратитесь к владельцам для уточнения их расписания.\n"
                    "Попробуйте позже или свяжитесь с администратором."
                )
                return
        
        # Create keyboard with available slots
        keyboard = []
        message_text = "Доступные слоты для встреч:\n\n"
        
        for date_str, slots in available_slots.items():
            if slots:  # Only show dates with available slots
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                day_name = date_obj.strftime('%A')
                formatted_date = date_obj.strftime('%d.%m.%Y')
                
                message_text += f"📅 **{day_name}, {formatted_date}**\n"
                
                row = []
                for slot in slots:
                    callback_data = f"book_{date_str}_{slot}"
                    row.append(InlineKeyboardButton(slot, callback_data=callback_data))
                    
                    if len(row) == 2:  # Two buttons per row
                        keyboard.append(row)
                        row = []
                
                if row:  # Add remaining buttons
                    keyboard.append(row)
                
                message_text += "\n"
        
        if not keyboard:
            await update.message.reply_text(
                "На доступные дни нет свободных слотов."
            )
            return
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error getting available slots: {e}")
        await update.message.reply_text(
            "Произошла ошибка при получении доступных слотов. Попробуйте позже."
        )

async def handle_booking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle slot booking callback."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data  # format: book_2024-01-15_14:00
    
    try:
        _, date_str, time_str = callback_data.split('_')
        
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user or user.status != UserStatus.ACTIVE:
                await query.edit_message_text(
                    "Нельзя назначить встречу в неактивном статусе."
                )
                return
            
            # Check if user already has a meeting scheduled for next 2 weeks
            two_weeks_ago = datetime.now() - timedelta(days=14)
            recent_meeting = db.query(Meeting).filter(
                and_(
                    Meeting.manager_id == user.id,
                    Meeting.scheduled_time > two_weeks_ago,
                    Meeting.status == MeetingStatus.SCHEDULED
                )
            ).first()
            
            if recent_meeting:
                next_allowed = recent_meeting.scheduled_time + timedelta(days=14)
                await query.edit_message_text(
                    f"У вас уже есть запланированная встреча.\n\n"
                    f"Следующую встречу можно назначить не ранее {next_allowed.strftime('%d.%m.%Y')}."
                )
                return
        
        # Create meeting
        calendar_service = GoogleCalendarService()
        meeting_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Double-check slot availability
        if not calendar_service.check_slot_availability(meeting_date, time_str):
            await query.edit_message_text(
                "К сожалению, этот слот уже занят. Попробуйте выбрать другое время."
            )
            return
        
        # Create meeting in Google Calendar
        event_id, meet_link = calendar_service.create_meeting(
            f"{user.first_name} {user.last_name}",
            user.department.value,  # Convert enum to string
            meeting_date,
            time_str,
            user.email  # Pass manager's email
        )
        
        # Save to database
        hour, minute = map(int, time_str.split(':'))
        scheduled_time = meeting_date.replace(hour=hour, minute=minute)
        
        with get_db() as db:
            meeting = Meeting(
                manager_id=user.id,
                scheduled_time=scheduled_time,
                google_event_id=event_id,
                google_meet_link=meet_link,
                status=MeetingStatus.SCHEDULED
            )
            db.add(meeting)
            db.commit()
            
            # Schedule reminders
            reminder_service = ReminderService()
            await reminder_service.schedule_meeting_reminders(meeting.id)
            await reminder_service.schedule_next_meeting_reminders(user.id, scheduled_time)
        
        # Notify admins
        for admin_id in settings.admin_ids_list:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"📅 Новая встреча\n\n"
                         f"👤 {user.first_name} {user.last_name}\n"
                         f"🏢 {user.department}\n"
                         f"📅 {scheduled_time.strftime('%d.%m.%Y в %H:%M')}\n"
                         f"🔗 {meet_link}"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
        
        await query.edit_message_text(
            f"Встреча успешно назначена!\n\n"
            f"📅 Дата: {scheduled_time.strftime('%d.%m.%Y')}\n"
            f"⏰ Время: {time_str}\n"
            f"🔗 Google Meet: {meet_link}\n\n"
            f"Вы получите напоминание за 1 час до встречи."
        )
        
    except Exception as e:
        logger.error(f"Error booking meeting: {e}")
        await query.edit_message_text(
            "Произошла ошибка при назначении встречи. Попробуйте позже."
        )

@require_registration
async def show_my_meetings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's scheduled meetings."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        meetings = db.query(Meeting).filter(
            and_(
                Meeting.manager_id == user.id,
                Meeting.status == MeetingStatus.SCHEDULED,
                Meeting.scheduled_time > datetime.now()
            )
        ).order_by(Meeting.scheduled_time).all()
        
        if not meetings:
            await update.message.reply_text(
                "У вас нет запланированных встреч. Нажмите /schedule для назначения новой встречи."
            )
            return
        
        message_text = "Ваши запланированные встречи:\n\n"
        
        keyboard = []
        for meeting in meetings:
            time_str = meeting.scheduled_time.strftime('%d.%m.%Y в %H:%M')
            message_text += f"📅 {time_str}\n"
            
            # Add cancel button
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ Отменить {meeting.scheduled_time.strftime('%d.%m')}",
                    callback_data=f"cancel_{meeting.id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await update.message.reply_text(message_text, reply_markup=reply_markup)

async def handle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle meeting cancellation."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    meeting_id = int(query.data.split('_')[1])
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        meeting = db.query(Meeting).filter(
            and_(
                Meeting.id == meeting_id,
                Meeting.manager_id == user.id
            )
        ).first()
        
        if not meeting:
            await query.edit_message_text(
                "Встреча не найдена."
            )
            return
        
        # Cancel in Google Calendar
        try:
            calendar_service = GoogleCalendarService()
            calendar_service.cancel_meeting(meeting.google_event_id)
        except Exception as e:
            logger.error(f"Error canceling Google Calendar event: {e}")
        
        # Update database
        meeting.status = MeetingStatus.CANCELLED
        db.commit()
        
        # Cancel related reminders
        db.query(Reminder).filter(
            Reminder.meeting_id == meeting.id
        ).update({'sent': True})
        db.commit()
        
        await query.edit_message_text(
            f"❌ Встреча отменена\n\n"
            f"📅 {meeting.scheduled_time.strftime('%d.%m.%Y в %H:%M')}\n\n"
            f"Можете назначить новую встречу через /schedule"
        )

# Status management functions
@require_registration
async def set_vacation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user status to vacation."""
    await _set_user_status(update, context, UserStatus.VACATION, "В отпуске")

@require_registration
async def set_sick_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user status to sick leave."""
    await _set_user_status(update, context, UserStatus.SICK_LEAVE, "На больничном")

@require_registration
async def set_business_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user status to business trip."""
    await _set_user_status(update, context, UserStatus.BUSINESS_TRIP, "В командировке")

@require_registration
async def set_active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user status to active."""
    await _set_user_status(update, context, UserStatus.ACTIVE, "Активный")

async def _set_user_status(update: Update, context: ContextTypes.DEFAULT_TYPE, status: UserStatus, status_text: str):
    """Helper function to set user status."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        old_status = user.status
        user.status = status
        db.commit()
        
        await update.message.reply_text(
            f"Ваш статус изменен на: {status_text}"
        )
        
        # If returning from non-active status, schedule reminder for next meeting
        if old_status != UserStatus.ACTIVE and status == UserStatus.ACTIVE:
            last_meeting = db.query(Meeting).filter(
                and_(
                    Meeting.manager_id == user.id,
                    Meeting.status == MeetingStatus.COMPLETED
                )
            ).order_by(Meeting.scheduled_time.desc()).first()
            
            if last_meeting:
                reminder_service = ReminderService()
                await reminder_service.schedule_next_meeting_reminders(
                    user.id, last_meeting.scheduled_time
                )

@require_registration
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get meeting statistics
        total_meetings = db.query(Meeting).filter(Meeting.manager_id == user.id).count()
        completed_meetings = db.query(Meeting).filter(
            and_(
                Meeting.manager_id == user.id,
                Meeting.status == MeetingStatus.COMPLETED
            )
        ).count()
        
        last_meeting = db.query(Meeting).filter(
            Meeting.manager_id == user.id
        ).order_by(Meeting.scheduled_time.desc()).first()
        
        status_emoji = {
            UserStatus.ACTIVE: "✅",
            UserStatus.VACATION: "🏖️",
            UserStatus.SICK_LEAVE: "🏥",
            UserStatus.BUSINESS_TRIP: "✈️"
        }.get(user.status, "❓")
        
        profile_text = (
            f"👤 **Мой профиль**\n\n"
            f"📝 Имя: {user.first_name} {user.last_name}\n"
            f"🏢 Отдел: {user.department}\n"
            f"{status_emoji} Статус: {user.status.value}\n\n"
            f"📊 **Статистика:**\n"
            f"📈 Всего встреч: {total_meetings}\n"
            f"✅ Проведено: {completed_meetings}\n"
        )
        
        if last_meeting:
            profile_text += f"📅 Последняя встреча: {last_meeting.scheduled_time.strftime('%d.%m.%Y')}\n"
        
        await update.message.reply_text(profile_text, parse_mode='Markdown')