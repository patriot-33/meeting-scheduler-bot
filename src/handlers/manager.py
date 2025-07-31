from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from datetime import datetime, timedelta, date
import logging
import traceback

from database import get_db, User, UserRole, UserStatus, Meeting, MeetingStatus
from services.meeting_service import MeetingService
from services.google_calendar import google_calendar_service
from services.reminder_service import ReminderService
from config import settings
from utils.decorators import require_registration

logger = logging.getLogger(__name__)

# MeetingService will be initialized in functions with DB context

async def notify_owners_about_meeting(context: ContextTypes.DEFAULT_TYPE, meeting, manager: User):
    """Send telegram notification to all owners about new meeting."""
    try:
        from services.owner_service import OwnerService
        
        owners = OwnerService.get_all_owners()
        if not owners:
            logger.warning("No owners found to notify")
            return
        
        # Format meeting details
        formatted_date = meeting.scheduled_time.strftime('%d.%m.%Y')
        formatted_time = meeting.scheduled_time.strftime('%H:%M')
        day_name = meeting.scheduled_time.strftime('%A')
        
        # Russian day names
        russian_days = {
            'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда',
            'Thursday': 'Четверг', 'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье'
        }
        russian_day = russian_days.get(day_name, day_name)
        
        message = f"""🔔 НОВАЯ ВСТРЕЧА ЗАПЛАНИРОВАНА!

📅 {russian_day}, {formatted_date}
🕐 {formatted_time}
👤 {manager.first_name} {manager.last_name}
🏢 {manager.department.value}

ID встречи: {meeting.id}"""
        
        if meeting.google_meet_link:
            message += f"\n🔗 Google Meet: {meeting.google_meet_link}"
        
        # Send notification to all owners
        for owner in owners:
            try:
                await context.bot.send_message(
                    chat_id=owner.telegram_id,
                    text=message,
                    parse_mode='HTML'
                )
                logger.info(f"✅ Notification sent to owner {owner.telegram_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to owner {owner.telegram_id}: {e}")
                
    except Exception as e:
        logger.error(f"Failed to notify owners: {e}")

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
        
        # CRITICAL: Check if manager has connected Google Calendar
        if not user.email:
            await update.message.reply_text(
                "⚠️ ТРЕБУЕТСЯ ПОДКЛЮЧЕНИЕ GOOGLE CALENDAR\n\n"
                "Для планирования встреч необходимо подключить ваш Google Calendar.\n"
                "Используйте команду /calendar для настройки.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Подключить календарь", callback_data="connect_calendar")]
                ])
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
    
    # Get user from database instead of context.user_data
    user = None
    if update.effective_user:
        user_id = update.effective_user.id
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
    
    await show_available_slots_inline(query, user)

async def show_available_slots_inline(query, user=None):
    """Helper function to show date selection inline with calendar validation."""
    try:
        # Check calendar requirement if user provided
        if user and not user.email:
            await query.edit_message_text(
                "⚠️ ТРЕБУЕТСЯ ПОДКЛЮЧЕНИЕ GOOGLE CALENDAR\n\n"
                "Для планирования встреч необходимо подключить ваш Google Calendar.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Подключить календарь", callback_data="connect_calendar")]
                ])
            )
            return
            
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

@require_registration
async def show_my_meetings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's scheduled meetings with cancellation options."""
    try:
        # Get user from database instead of context.user_data
        user_id = update.effective_user.id
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                error_msg = "❌ Пользователь не найден"
                if update.callback_query:
                    await update.callback_query.answer(error_msg)
                else:
                    await update.message.reply_text(error_msg)
                return
            
            # Get user's meetings
            meetings = db.query(Meeting).filter(
                Meeting.manager_id == user.id,
                Meeting.status == MeetingStatus.SCHEDULED,
                Meeting.scheduled_time > datetime.now()
            ).order_by(Meeting.scheduled_time).all()
        
        if not meetings:
            no_meetings_msg = "📅 У вас нет запланированных встреч"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="manager_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    no_meetings_msg,
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    no_meetings_msg,
                    reply_markup=reply_markup
                )
            return
        
        # Build meetings list with cancel buttons
        keyboard = []
        text = "📅 ВАШИ ЗАПЛАНИРОВАННЫЕ ВСТРЕЧИ:\n\n"
        
        for meeting in meetings:
            formatted_date = meeting.scheduled_time.strftime('%d.%m.%Y')
            formatted_time = meeting.scheduled_time.strftime('%H:%M')
            day_name = meeting.scheduled_time.strftime('%A')
            
            # Russian day names
            russian_days = {
                'Monday': 'Пн', 'Tuesday': 'Вт', 'Wednesday': 'Ср',
                'Thursday': 'Чт', 'Friday': 'Пт', 'Saturday': 'Сб', 'Sunday': 'Вс'
            }
            russian_day = russian_days.get(day_name, day_name)
            
            text += f"🗓 {russian_day} {formatted_date} в {formatted_time}\n"
            text += f"📋 ID: {meeting.id}\n"
            if meeting.google_meet_link:
                text += f"🔗 Google Meet\n"
            text += "\n"
            
            # Add cancel button for each meeting
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ Отменить встречу {formatted_date}", 
                    callback_data=f"cancel_meeting_{meeting.id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад в меню", callback_data="manager_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both callback query and regular message
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup
            )
        
    except Exception as e:
        logger.error(f"Error showing meetings: {e}")
        # Handle error response for both types
        error_msg = "❌ Ошибка при загрузке встреч"
        if update.callback_query:
            await update.callback_query.answer(error_msg)
        else:
            await update.message.reply_text(error_msg)

@require_registration
async def cancel_meeting_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle meeting cancellation."""
    try:
        query = update.callback_query
        if not query:
            await update.message.reply_text("❌ Эта функция доступна только через меню встреч")
            return
            
        meeting_id = int(query.data.split('_')[2])
        
        # Get user from database instead of context.user_data
        user_id = update.effective_user.id
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await query.answer("❌ Пользователь не найден")
            return
        
        # Verify meeting belongs to user
        with get_db() as db:
            meeting = db.query(Meeting).filter(
                Meeting.id == meeting_id,
                Meeting.manager_id == user.id,
                Meeting.status == MeetingStatus.SCHEDULED
            ).first()
            
            if not meeting:
                await query.answer("❌ Встреча не найдена или уже отменена")
                return
            
            # Check if meeting is too soon (less than 2 hours)
            time_until_meeting = meeting.scheduled_time - datetime.now()
            if time_until_meeting.total_seconds() < 7200:  # 2 hours
                await query.answer("❌ Нельзя отменить встречу менее чем за 2 часа")
                return
            
            # Cancel the meeting
            meeting_service = MeetingService(db)
            success = meeting_service.cancel_meeting(meeting.id)
            
            if success:
                # Notify owners about cancellation
                await notify_owners_about_cancellation(context, meeting, user)
                
                await query.answer("✅ Встреча успешно отменена")
                # Refresh the meetings list
                await show_my_meetings(update, context)
            else:
                await query.answer("❌ Ошибка при отмене встречи")
                
    except Exception as e:
        logger.error(f"Error cancelling meeting: {e}")
        await update.callback_query.answer("❌ Ошибка при отмене встречи")

async def notify_owners_about_cancellation(context: ContextTypes.DEFAULT_TYPE, meeting, manager: User):
    """Notify owners about meeting cancellation."""
    try:
        from services.owner_service import OwnerService
        
        owners = OwnerService.get_all_owners()
        if not owners:
            return
        
        formatted_date = meeting.scheduled_time.strftime('%d.%m.%Y')
        formatted_time = meeting.scheduled_time.strftime('%H:%M')
        
        message = f"""🚫 ВСТРЕЧА ОТМЕНЕНА!

📅 {formatted_date} в {formatted_time}
👤 {manager.first_name} {manager.last_name}
🏢 {manager.department.value}

ID встречи: {meeting.id}"""
        
        for owner in owners:
            if owner.telegram_id:
                try:
                    await context.bot.send_message(
                        chat_id=owner.telegram_id,
                        text=message
                    )
                except Exception as e:
                    logger.error(f"Failed to notify owner {owner.id}: {e}")
                    
    except Exception as e:
        logger.error(f"Error notifying owners about cancellation: {e}")

@require_registration
async def show_manager_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show manager main menu."""
    try:
        keyboard = [
            [InlineKeyboardButton("📅 Запланировать встречу", callback_data="schedule_meeting")],
            [InlineKeyboardButton("🗓 Мои встречи", callback_data="my_meetings")],
        ]
        
        text = f"👨‍💼 МЕНЮ МЕНЕДЖЕРА\n\n👤 Выберите действие:"
        
        # Handle both callback query and regular message
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
    except Exception as e:
        logger.error(f"Error showing manager menu: {e}")
        # Handle error response for both types
        error_msg = "❌ Ошибка при загрузке меню"
        if update.callback_query:
            await update.callback_query.answer(error_msg)
        else:
            await update.message.reply_text(error_msg)

async def show_available_slots_inline_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wrapper for show_available_slots_inline that handles user fetching."""
    query = update.callback_query
    if query:
        # Get user from database instead of context.user_data
        user = None
        if update.effective_user:
            user_id = update.effective_user.id
            with get_db() as db:
                user = db.query(User).filter(User.telegram_id == user_id).first()
        await show_available_slots_inline(query, user)

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
        logger.info(f"🔍 DEBUG: Checking slot availability for {meeting_datetime}")
        slot_available = meeting_service.is_slot_available(meeting_datetime)
        logger.info(f"🔍 DEBUG: Slot availability result: {slot_available}")
        
        if not slot_available:
            await query.edit_message_text(
                "❌ К сожалению, этот слот уже занят. Выберите другое время."
            )
            return
        
        # Create meeting
        try:
            logger.info(f"🔍 DEBUG: Starting meeting creation for user {user.id} at {meeting_datetime}")
            meeting = meeting_service.create_meeting(user.id, meeting_datetime)
            logger.info(f"🔍 DEBUG: Meeting service returned: {meeting}")
            
            if meeting:
                # CRITICAL FIX: Send telegram notifications to owners
                await notify_owners_about_meeting(context, meeting, user)
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
                logger.error(f"🔍 DEBUG: Meeting service returned None/False for user {user.id}")
                await query.edit_message_text(
                    "❌ Не удалось создать встречу. Попробуйте позже или обратитесь к администратору."
                )
                
        except Exception as e:
            logger.error(f"🔍 DEBUG: Exception creating meeting for user {user.id}: {type(e).__name__}: {e}")
            logger.error(f"🔍 DEBUG: Meeting creation traceback: {traceback.format_exc()}")
            
            # Enhanced diagnostics
            try:
                import psutil
                logger.error(f"🔍 SYSTEM: CPU {psutil.cpu_percent()}%, Memory {psutil.virtual_memory().percent}%")
                logger.error(f"🔍 CONTEXT: User {user.first_name} {user.last_name}, Time {booking_time}")
                logger.error(f"🔍 CALENDAR: Service available? {google_calendar_service.is_available}")
            except Exception as diag_error:
                logger.error(f"🔍 DIAGNOSTIC ERROR: {diag_error}")
            
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
        CallbackQueryHandler(show_my_meetings, pattern='^my_meetings$'),
        CallbackQueryHandler(show_manager_menu, pattern='^manager_menu$'),
        CallbackQueryHandler(cancel_meeting_callback, pattern=r'^cancel_meeting_\d+$'),
        CallbackQueryHandler(lambda u, c: show_available_slots(u, c), pattern='^schedule_meeting$'),
        CallbackQueryHandler(lambda u, c: show_available_slots_inline_wrapper(u, c), pattern='^schedule_meeting_inline$'),
    ]