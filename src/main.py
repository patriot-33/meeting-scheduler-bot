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
from src.handlers import registration, admin, manager, common
from src.services.reminder_service import ReminderService
from src.utils.scheduler import setup_scheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.log_level)
)
logger = logging.getLogger(__name__)

async def error_handler(update: Update, context):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте позже или свяжитесь с администратором."
        )

def main():
    """Start the bot."""
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
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
    application.add_handler(CallbackQueryHandler(manager.handle_booking_callback, pattern="^book_"))
    application.add_handler(CallbackQueryHandler(manager.handle_cancel_callback, pattern="^cancel_"))
    application.add_handler(CallbackQueryHandler(common.handle_navigation_callback, pattern="^nav_"))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Setup scheduler for reminders
    scheduler = setup_scheduler(application)
    scheduler.start()
    
    # Run the bot
    if settings.webhook_url:
        # Webhook mode for production
        application.run_webhook(
            listen="0.0.0.0",
            port=settings.port,
            url_path=settings.webhook_path,
            webhook_url=f"{settings.webhook_url}{settings.webhook_path}",
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        # Polling mode for development
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()