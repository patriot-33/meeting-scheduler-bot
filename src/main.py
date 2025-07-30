import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from config import settings
from database import init_db
from handlers import registration, admin, manager, common, owner, manager_calendar
from services.reminder_service import ReminderService
from utils.scheduler import setup_scheduler

# Configure logging for small team
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.log_level),
    handlers=[
        logging.StreamHandler(),  # Console output for render.com
        logging.FileHandler('bot.log', encoding='utf-8') if settings.debug else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set third-party loggers to WARNING to reduce noise
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('googleapiclient').setLevel(logging.WARNING)

async def error_handler(update: Update, context):
    """Log errors caused by updates."""
    from sqlalchemy.exc import DataError, IntegrityError, DatabaseError, OperationalError
    from telegram.error import TelegramError, NetworkError, TimedOut
    
    error_type = type(context.error).__name__
    user_id = update.effective_user.id if update and update.effective_user else "Unknown"
    
    # Handle specific database errors
    if isinstance(context.error, (DataError, IntegrityError)):
        logger.error(f"Database integrity error for user {user_id}: {error_type} - {str(context.error)}")
        user_message = "⚠️ Ошибка обработки данных. Проверьте корректность введенной информации."
    elif isinstance(context.error, (DatabaseError, OperationalError)):
        logger.error(f"Database connection error for user {user_id}: {error_type} - {str(context.error)}")
        user_message = "⚠️ Временная проблема с базой данных. Попробуйте через несколько секунд."
    elif isinstance(context.error, (NetworkError, TimedOut)):
        logger.error(f"Network/timeout error for user {user_id}: {error_type}")
        user_message = "⚠️ Проблема с подключением. Попробуйте еще раз."
    elif isinstance(context.error, TelegramError):
        logger.error(f"Telegram API error for user {user_id}: {error_type} - {str(context.error)}")
        user_message = "⚠️ Ошибка Telegram API. Попробуйте позже."
    elif "callback_data" in str(context.error).lower():
        logger.error(f"Callback data error for user {user_id}: {error_type}")
        user_message = "⚠️ Устаревшая кнопка. Используйте /owner для обновления меню."
    else:
        # Don't log sensitive update data in production
        if settings.debug:
            logger.error(f"Update {update} caused error {context.error}")
        else:
            logger.error(f"Generic error for user {user_id}: {error_type}")
        user_message = "⚠️ Произошла техническая ошибка. Попробуйте позже."
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(user_message)
        except Exception as e:
            logger.error(f"Failed to send error message to user {user_id}: {e}")
    elif update and update.callback_query:
        try:
            await update.callback_query.answer(user_message, show_alert=True)
        except Exception as e:
            logger.error(f"Failed to answer callback query for user {user_id}: {e}")

def main():
    """Start the bot."""
    logger.info("🚀 Starting Meeting Scheduler Bot for team...")
    
    # Health check before startup
    from utils.health_check import health_check
    health = health_check()
    if health['status'] != 'healthy':
        logger.error(f"❌ Health check failed: {health}")
        return
    
    # Initialize database
    try:
        # Initialize database (enum hotfix handled internally by database.py)
        if settings.database_url.startswith('postgresql') and settings.force_enum_hotfix:
            logger.info("🔥 Running enum hotfix for PostgreSQL compatibility...")
            logger.info("✅ Enum hotfix will be handled by database initialization")
        
        init_db()
        logger.info("✅ Database initialized")
        
        # Auto-restore is handled by database.py during initialization
        if settings.database_url.startswith('postgresql'):
            logger.info("🔄 Database initialization includes data consistency checks")
                
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return
    
    # Create application
    application = Application.builder().token(settings.bot_token).build()
    
    # Add handlers
    # ConversationHandlers first (highest priority)
    application.add_handler(registration.get_registration_handler())
    application.add_handler(owner.get_owner_conversation_handler())
    
    # Callback query handlers (medium priority)
    application.add_handler(CallbackQueryHandler(admin.handle_admin_callback, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(owner.handle_owner_callback, pattern="^owner_"))
    application.add_handler(CallbackQueryHandler(manager.handle_booking_callback, pattern="^book_"))
    application.add_handler(CallbackQueryHandler(manager.handle_cancel_callback, pattern="^cancel_"))
    application.add_handler(CallbackQueryHandler(manager_calendar.handle_calendar_callback, pattern="^(send_email_to_owner|calendar_faq|connect_calendar)$"))
    application.add_handler(CallbackQueryHandler(common.handle_navigation_callback, pattern="^nav_"))
    
    # Command handlers (lowest priority)
    # Start command
    application.add_handler(CommandHandler("start", common.start_command))
    application.add_handler(CommandHandler("help", common.help_command))
    application.add_handler(CommandHandler("cancel", common.cancel_command))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin.admin_menu))
    application.add_handler(CommandHandler("pending", admin.show_pending_users))
    application.add_handler(CommandHandler("users", admin.list_users))
    application.add_handler(CommandHandler("stats", admin.show_statistics))
    application.add_handler(CommandHandler("broadcast", admin.broadcast_message))
    application.add_handler(CommandHandler("notifications", admin.toggle_notifications))
    
    # Owner commands
    application.add_handler(CommandHandler("owner", owner.owner_menu))
    
    # Manager commands
    application.add_handler(CommandHandler("schedule", manager.show_available_slots))
    application.add_handler(CommandHandler("my_meetings", manager.show_my_meetings))
    application.add_handler(CommandHandler("vacation", manager.set_vacation))
    application.add_handler(CommandHandler("sick", manager.set_sick_leave))
    application.add_handler(CommandHandler("trip", manager.set_business_trip))
    application.add_handler(CommandHandler("active", manager.set_active))
    application.add_handler(CommandHandler("profile", manager.show_profile))
    application.add_handler(CommandHandler("calendar", manager_calendar.connect_calendar))
    application.add_handler(CommandHandler("email", manager_calendar.save_manager_email))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Setup scheduler for reminders
    try:
        scheduler = setup_scheduler(application)
        scheduler.start()
        logger.info("✅ Scheduler started")
    except Exception as e:
        logger.error(f"❌ Scheduler setup failed: {e}")
        return
    
    # Run the bot
    try:
        if settings.webhook_url:
            webhook_full_url = f"{settings.webhook_url}{settings.webhook_path}"
            logger.info(f"🌐 Starting webhook mode on port {settings.port}")
            logger.info(f"🔗 Webhook URL: {webhook_full_url}")
            # Webhook mode for production
            application.run_webhook(
                listen="0.0.0.0",
                port=settings.port,
                url_path=settings.webhook_path,
                webhook_url=webhook_full_url,
                allowed_updates=Update.ALL_TYPES,
            )
        else:
            logger.info("🔄 Starting polling mode for development")
            # Polling mode for development
            application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}")
        try:
            scheduler.shutdown()
        except Exception as shutdown_error:
            logger.error(f"❌ Scheduler shutdown error: {shutdown_error}")
        raise

if __name__ == '__main__':
    main()