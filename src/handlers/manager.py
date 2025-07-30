from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from datetime import datetime, timedelta, date
import logging

from database import get_db, User, UserRole, UserStatus, Meeting, MeetingStatus
from services.meeting_service import MeetingService
from services.google_calendar import google_calendar_service
from services.reminder_service import ReminderService
from config import settings
from utils.decorators import require_registration

logger = logging.getLogger(__name__)

# Русские названия дней недели
RUSSIAN_WEEKDAYS = {
    'Monday': 'Понедельник',
    'Tuesday': 'Вторник', 
    'Wednesday': 'Среда',
    'Thursday': 'Четверг',
    'Friday': 'Пятница',
    'Saturday': 'Суббота',
    'Sunday': 'Воскресенье'
}

@require_registration
async def show_available_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available dates for meetings."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if user.role != UserRole.MANAGER:
            await update.message.reply_text(
                "❌ Данная функция доступна только руководителям отделов."
            )
            return
        
        # Check user status
        if user.status != UserStatus.ACTIVE:
            await update.message.reply_text(
                "⏸ Вы находитесь в неактивном статусе.\n"
                f"Для назначения встреч сначала вернитесь в активный статус: /active"
            )
            return
    
    try:
        with get_db() as db:
            meeting_service = MeetingService(db)
            
            # Get available slots when owners are free
            available_slots = meeting_service.get_available_slots(days_ahead=14)
            
            if not available_slots:
                await update.message.reply_text(
                    "❌ К сожалению, на ближайшие 2 недели нет свободных слотов.\n\n"
                    "🕐 Слоты доступны только когда свободны владельцы бизнеса.\n"
                    "📞 Обратитесь к владельцам для уточнения их расписания.\n"
                    "Попробуйте позже или свяжитесь с администратором."
                )
                return
        
        # Create keyboard with available dates (only days, not time slots)
        keyboard = []
        message_text = "📅 Выберите день для встречи:\n\n"
        
        sorted_dates = sorted(available_slots.keys())
        
        for date_str in sorted_dates:
            slots = available_slots[date_str]
            if slots:  # Only show dates with available slots
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                english_day = date_obj.strftime('%A')
                russian_day = RUSSIAN_WEEKDAYS.get(english_day, english_day)
                formatted_date = date_obj.strftime('%d.%m.%Y')
                
                # Show day with number of available slots
                button_text = f"{russian_day}, {formatted_date} ({len(slots)} слотов)"
                callback_data = f"date_{date_str}"
                
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        if not keyboard:
            await update.message.reply_text(
                "На доступные дни нет свободных слотов."
            )
            return
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error showing available slots: {e}")
        await update.message.reply_text(
            "Произошла ошибка при загрузке слотов. Попробуйте позже."
        )

async def show_day_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available time slots for selected date."""
    query = update.callback_query
    await query.answer()
    
    # Extract date from callback data
    date_str = query.data.replace('date_', '')
    
    try:
        with get_db() as db:
            meeting_service = MeetingService(db)
            available_slots = meeting_service.get_available_slots(days_ahead=14)
            
            if date_str not in available_slots:
                await query.edit_message_text(
                    "❌ К сожалению, на этот день слоты больше недоступны."
                )
                return
            
            slots = available_slots[date_str]
            if not slots:
                await query.edit_message_text(
                    "❌ На этот день нет доступных слотов."
                )
                return
            
            # Format date for display
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            english_day = date_obj.strftime('%A')
            russian_day = RUSSIAN_WEEKDAYS.get(english_day, english_day)
            formatted_date = date_obj.strftime('%d.%m.%Y')
            
            # Create keyboard with time slots
            keyboard = []
            message_text = f"🕐 Выберите время на {russian_day}, {formatted_date}:\n\n"
            
            # Group slots in rows of 3
            row = []
            for slot in slots:
                callback_data = f"book_{date_str}_{slot}"
                row.append(InlineKeyboardButton(slot, callback_data=callback_data))
                
                if len(row) == 3:  # Three time slots per row
                    keyboard.append(row)
                    row = []
            
            if row:  # Add remaining buttons
                keyboard.append(row)
            
            # Add back button
            keyboard.append([InlineKeyboardButton("← Назад к выбору дня", callback_data="back_to_dates")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message_text,
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logger.error(f"Error showing day slots: {e}")
        await query.edit_message_text(
            "Произошла ошибка при загрузке слотов. Попробуйте позже."
        )

async def back_to_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to date selection."""
    query = update.callback_query
    await query.answer()
    
    # Re-show the date selection
    await show_available_slots_inline(query)

async def show_available_slots_inline(query):
    """Helper function to show date selection inline."""
    try:
        with get_db() as db:
            meeting_service = MeetingService(db)
            available_slots = meeting_service.get_available_slots(days_ahead=14)
            
            if not available_slots:
                await query.edit_message_text(
                    "❌ К сожалению, нет доступных слотов."
                )
                return
        
        # Create keyboard with available dates
        keyboard = []
        message_text = "📅 Выберите день для встречи:\n\n"
        
        sorted_dates = sorted(available_slots.keys())
        
        for date_str in sorted_dates:
            slots = available_slots[date_str]
            if slots:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                english_day = date_obj.strftime('%A')
                russian_day = RUSSIAN_WEEKDAYS.get(english_day, english_day)
                formatted_date = date_obj.strftime('%d.%m.%Y')
                
                button_text = f"{russian_day}, {formatted_date} ({len(slots)} слотов)"
                callback_data = f"date_{date_str}"
                
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error showing available slots inline: {e}")
        await query.edit_message_text(
            "Произошла ошибка при загрузке слотов. Попробуйте позже."
        )

async def book_meeting_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Book a specific meeting slot."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Parse callback data: book_2025-01-15_14:00
    callback_parts = query.data.split('_')
    if len(callback_parts) != 3:
        await query.edit_message_text("❌ Ошибка в данных слота.")
        return
        
    date_str = callback_parts[1]
    time_str = callback_parts[2]
    
    try:
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await query.edit_message_text("❌ Пользователь не найден.")
                return
            
            meeting_service = MeetingService(db)
            
            # Parse meeting datetime
            meeting_date = datetime.strptime(date_str, '%Y-%m-%d')
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            meeting_datetime = datetime.combine(meeting_date.date(), time_obj)
            
            # Check if user already has a meeting this week
            week_start = meeting_date - timedelta(days=meeting_date.weekday())
            week_end = week_start + timedelta(days=6)
            
            existing_meeting = db.query(Meeting).filter(
                Meeting.manager_id == user.id,
                Meeting.scheduled_time >= week_start,
                Meeting.scheduled_time <= week_end,
                Meeting.status == MeetingStatus.SCHEDULED
            ).first()
            
            if existing_meeting:
                next_allowed = existing_meeting.scheduled_time + timedelta(days=7)
                await query.edit_message_text(
                    f"⚠️ У вас уже есть запланированная встреча на эту неделю.\n"
                    f"Следующую встречу можно назначить не ранее {next_allowed.strftime('%d.%m.%Y')}."
                )
                return
        
        # Check slot availability using meeting service
        if not meeting_service.is_slot_available(meeting_datetime):
            await query.edit_message_text(
                "❌ К сожалению, этот слот уже занят. Выберите другое время."
            )
            return
        
        # Create meeting
        try:
            meeting = meeting_service.create_meeting(user.id, meeting_datetime)
            
            if meeting:
                # Format success message
                english_day = meeting_datetime.strftime('%A')
                russian_day = RUSSIAN_WEEKDAYS.get(english_day, english_day)
                formatted_date = meeting_datetime.strftime('%d.%m.%Y')
                
                success_message = (
                    f"✅ Встреча успешно запланирована!\n\n"
                    f"📅 {russian_day}, {formatted_date}\n"
                    f"🕐 {time_str}\n"
                    f"👤 {user.first_name} {user.last_name}\n"
                    f"🏢 {user.department.value}\n\n"
                )
                
                # Add Google Meet link if available
                if meeting.google_meet_link:
                    success_message += f"🔗 [Ссылка на встречу]({meeting.google_meet_link})\n\n"
                
                success_message += (
                    "📧 Приглашения отправлены всем участникам.\n"
                    "⏰ Напоминания будут отправлены за 7, 3 и 1 день до встречи."
                )
                
                await query.edit_message_text(
                    success_message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                
                logger.info(f"Meeting created successfully: {meeting.id}")
                
            else:
                await query.edit_message_text(
                    "❌ Не удалось создать встречу. Попробуйте позже или обратитесь к администратору."
                )
                
        except Exception as e:
            logger.error(f"Error creating meeting: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при создании встречи. Попробуйте позже."
            )
                
    except Exception as e:
        logger.error(f"Error booking meeting: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при бронировании встречи. Попробуйте позже."
        )

# Handler registration
def get_manager_handlers():
    """Return list of manager-related handlers."""
    return [
        CommandHandler('schedule', show_available_slots),
        CallbackQueryHandler(show_day_slots, pattern=r'^date_\d{4}-\d{2}-\d{2}$'),
        CallbackQueryHandler(back_to_dates, pattern='^back_to_dates$'),
        CallbackQueryHandler(book_meeting_slot, pattern=r'^book_\d{4}-\d{2}-\d{2}_\d{2}:\d{2}$'),
    ]