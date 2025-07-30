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

from src.config import settings
from src.database import init_db
from src.handlers import registration, admin, manager, common, owner
from src.services.reminder_service import ReminderService
from src.utils.scheduler import setup_scheduler

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
    from sqlalchemy.exc import DataError, IntegrityError, DatabaseError
    
    error_type = type(context.error).__name__
    
    # Handle specific database errors
    if isinstance(context.error, (DataError, IntegrityError, DatabaseError)):
        logger.error(f"Database error occurred: {error_type} - {str(context.error)}")
        user_message = "⚠️ Ошибка обработки данных. Проверьте корректность введенной информации."
    else:
        # Don't log sensitive update data in production
        if settings.debug:
            logger.error(f"Update {update} caused error {context.error}")
        else:
            logger.error(f"Error occurred: {error_type}")
        user_message = "⚠️ Произошла техническая ошибка. Попробуйте позже."
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(user_message)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

def main():
    """Start the bot."""
    logger.info("🚀 Starting Meeting Scheduler Bot for team...")
    
    # Health check before startup
    from src.utils.health_check import health_check
    health = health_check()
    if health['status'] != 'healthy':
        logger.error(f"❌ Health check failed: {health}")
        return
    
    # Initialize database
    try:
        # Force run hotfix for enum compatibility on first startup
        if settings.database_url.startswith('postgresql') and settings.force_enum_hotfix:
            logger.info("🔥 Running enum hotfix for PostgreSQL compatibility...")
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from hotfix_enum import hotfix_enum_database
                hotfix_enum_database()
                logger.info("✅ Enum hotfix completed")
            except Exception as hotfix_error:
                logger.warning(f"⚠️ Hotfix failed, continuing with normal init: {hotfix_error}")
        
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return
    
    # Create application
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Add handlers
    # Start command
    application.add_handler(CommandHandler("start", common.start_command))
    application.add_handler(CommandHandler("help", common.help_command))
    application.add_handler(CommandHandler("cancel", common.cancel_command))
    
    # Registration conversation
    application.add_handler(registration.get_registration_handler())
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin.admin_menu))
    application.add_handler(CommandHandler("pending", admin.show_pending_users))
    application.add_handler(CommandHandler("users", admin.list_users))
    application.add_handler(CommandHandler("stats", admin.show_statistics))
    application.add_handler(CommandHandler("broadcast", admin.broadcast_message))
    application.add_handler(CommandHandler("notifications", admin.toggle_notifications))
    
    # Owner commands
    application.add_handler(CommandHandler("owner", owner.owner_menu))
    application.add_handler(owner.get_owner_conversation_handler())
    
    # Manager commands
    application.add_handler(CommandHandler("schedule", manager.show_available_slots))
    application.add_handler(CommandHandler("my_meetings", manager.show_my_meetings))
    application.add_handler(CommandHandler("vacation", manager.set_vacation))
    application.add_handler(CommandHandler("sick", manager.set_sick_leave))
    application.add_handler(CommandHandler("trip", manager.set_business_trip))
    application.add_handler(CommandHandler("active", manager.set_active))
    application.add_handler(CommandHandler("profile", manager.show_profile))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(admin.handle_admin_callback, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(owner.handle_owner_callback, pattern="^owner_"))
    application.add_handler(CallbackQueryHandler(manager.handle_booking_callback, pattern="^book_"))
    application.add_handler(CallbackQueryHandler(manager.handle_cancel_callback, pattern="^cancel_"))
    application.add_handler(CallbackQueryHandler(common.handle_navigation_callback, pattern="^nav_"))
    
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