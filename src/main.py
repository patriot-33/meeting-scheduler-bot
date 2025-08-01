import logging
import asyncio
import traceback
import sys
import psutil
import os
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from aiohttp import web
from aiohttp.web import Request

from config import settings
from database import init_db
from handlers import registration, admin, manager, common, owner, manager_calendar, manager_calendar_simple, check_oauth_status
from services.reminder_service import ReminderService
from utils.scheduler import setup_scheduler

# BULLETPROOF DIAGNOSTIC LOGGING
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('test_session.log', encoding='utf-8'),
        logging.FileHandler('debug_session.log', encoding='utf-8'), 
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_system_state():
    """Log system state for diagnostics"""
    logger.info(f"🔍 SYSTEM STATE:")
    logger.info(f"   CPU: {psutil.cpu_percent()}%")
    logger.info(f"   Memory: {psutil.virtual_memory().percent}%")
    logger.info(f"   Disk: {psutil.disk_usage('/').percent}%")
    
    # Try to get network connections, but handle permission issues on macOS
    try:
        connections_count = len(psutil.net_connections())
        logger.info(f"   Active connections: {connections_count}")
    except (psutil.AccessDenied, PermissionError) as e:
        logger.info(f"   Active connections: Permission denied on macOS - {e}")
    
    logger.info(f"   Python version: {sys.version}")
    logger.info(f"   Current time: {datetime.now()}")
    logger.info(f"   Working directory: {os.getcwd()}")

def debug_context(func_name, local_vars, step):
    """Debug context logging"""
    logger.debug(f"🔍 {func_name} - Step {step}")
    for var_name, var_value in local_vars.items():
        if var_name != 'self':  # Skip self references
            logger.debug(f"   {var_name}: {type(var_value).__name__} = {str(var_value)[:100]}...")

# Set third-party loggers to WARNING to reduce noise
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('googleapiclient').setLevel(logging.WARNING)

async def health_handler(request: Request):
    """Health check endpoint for deployment platforms."""
    from utils.health_check import health_check
    import json
    
    try:
        health_status = health_check()
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return web.json_response(health_status, status=status_code)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.json_response(
            {"status": "unhealthy", "error": str(e)}, 
            status=503
        )

async def error_handler(update: Update, context):
    """Log errors caused by updates."""
    logger.error("🚨 ERROR HANDLER: ========== ERROR OCCURRED ==========")
    
    from sqlalchemy.exc import DataError, IntegrityError, DatabaseError, OperationalError
    from telegram.error import TelegramError, NetworkError, TimedOut
    
    error_type = type(context.error).__name__
    user_id = update.effective_user.id if update and update.effective_user else "Unknown"
    
    logger.error(f"🚨 ERROR TYPE: {error_type}")
    logger.error(f"🚨 ERROR MESSAGE: {context.error}")
    logger.error(f"🚨 USER ID: {user_id}")
    logger.error(f"🚨 FULL TRACEBACK: {traceback.format_exc()}")
    
    if update:
        logger.error(f"🚨 UPDATE TYPE: {type(update)}")
        if update.message:
            logger.error(f"🚨 MESSAGE TEXT: {update.message.text}")
        if update.callback_query:
            logger.error(f"🚨 CALLBACK DATA: {update.callback_query.data}")
    else:
        logger.error("🚨 UPDATE: None")
    
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

async def main():
    """Start the bot with full diagnostics."""
    logger.info("🚀 STARTING MEETING SCHEDULER BOT WITH FULL DIAGNOSTICS...")
    
    # 🔍 ДИАГНОСТИКА 1: SYSTEM STATE
    log_system_state()
    debug_context("main", {"startup_stage": "init"}, 1)
    
    # Health check before startup
    from utils.health_check import health_check
    health = health_check()
    logger.info(f"🏥 HEALTH CHECK RESULT: {health}")
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
        
        # 🚨 CRITICAL FIX: Apply google_calendar_id migration if needed
        logger.info("🔧 APPLYING CRITICAL MIGRATION FIX...")
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Add project root to path
            from migrations.add_google_calendar_id_field import upgrade
            
            migration_success = upgrade()
            if migration_success:
                logger.info("✅ Critical migration applied successfully")
            else:
                logger.warning("⚠️ Critical migration may have failed, but continuing startup")
        except Exception as migration_error:
            logger.error(f"❌ Critical migration error: {migration_error}")
            logger.warning("⚠️ Continuing startup despite migration error")
        
        # Auto-restore is handled by database.py during initialization
        if settings.database_url.startswith('postgresql'):
            logger.info("🔄 Database initialization includes data consistency checks")
                
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return
    
    # Create application
    logger.info("🤖 BUILDING TELEGRAM APPLICATION...")
    application = Application.builder().token(settings.bot_token).build()
    logger.info("🤖 ✅ APPLICATION BUILT")
    
    # Add error handler first
    logger.info("🤖 ADDING ERROR HANDLER...")
    application.add_error_handler(error_handler)
    
    # Add handlers
    logger.info("🤖 ADDING CONVERSATION HANDLERS...")
    # ConversationHandlers first (highest priority)
    application.add_handler(registration.get_registration_handler())
    application.add_handler(owner.get_owner_conversation_handler())
    logger.info("🤖 ✅ CONVERSATION HANDLERS ADDED")
    
    # Callback query handlers (medium priority)
    application.add_handler(CallbackQueryHandler(admin.handle_admin_callback, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(owner.handle_owner_callback, pattern="^owner_"))
    # Note: manager booking callbacks are handled by get_manager_handlers() below
    application.add_handler(CallbackQueryHandler(manager_calendar.handle_calendar_callback, pattern="^(send_email_to_owner|calendar_faq|connect_calendar|reconnect_calendar|disconnect_calendar|connect_calendar_fresh)$"))
    application.add_handler(CallbackQueryHandler(owner.handle_owner_calendar_callback, pattern="^(connect_owner_calendar|reconnect_owner_calendar)$"))
    application.add_handler(CallbackQueryHandler(manager_calendar_simple.simple_calendar_faq, pattern="^simple_calendar_faq$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer("📋 Email скопирован!"), pattern="^copy_service_email:"))
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
    # Removed duplicate calendar handler - using unified handler below
    
    # Manager commands - new improved handlers
    for handler in manager.get_manager_handlers():
        application.add_handler(handler)
    
    # Additional manager commands (if they exist)
    manager_commands = [
        ("my_meetings", "show_my_meetings"),
        ("vacation", "set_vacation"),
        ("sick", "set_sick_leave"),
        ("trip", "set_business_trip"),
        ("active", "set_active"),
        ("profile", "show_profile")
    ]
    
    for command_name, function_name in manager_commands:
        try:
            handler_function = getattr(manager, function_name)
            application.add_handler(CommandHandler(command_name, handler_function))
        except AttributeError:
            logger.debug(f"Manager command '{command_name}' not available - skipping")
    # UNIFIED CALENDAR HANDLER - works for both owners and managers
    async def unified_calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unified handler for /calendar command that works for both owners and managers."""
        user_id = update.effective_user.id
        
        try:
            from database import get_db, User, UserRole
            with get_db() as db:
                user = db.query(User).filter(User.telegram_id == user_id).first()
                
                if not user:
                    await update.message.reply_text("❌ Вы не зарегистрированы в системе. Используйте /start")
                    return
                
                # Route to appropriate handler based on user role
                logger.info(f"🔍 DEBUG: unified_calendar_handler - User {user_id} has role {user.role.value}")
                if user.role == UserRole.OWNER:
                    logger.info(f"🔍 Routing /calendar to OWNER handler for user {user_id}")
                    await owner.connect_owner_calendar(update, context)
                elif user.role == UserRole.MANAGER:
                    logger.info(f"🔍 Routing /calendar to MANAGER handler for user {user_id}")
                    await manager_calendar.connect_calendar(update, context)
                else:
                    logger.warning(f"❌ Access denied: User {user_id} has role {user.role.value}, access only for OWNER/MANAGER")
                    await update.message.reply_text("❌ Функция подключения календаря доступна только владельцам и руководителям.")
        except Exception as e:
            logger.error(f"Error in unified_calendar_handler: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
    
    application.add_handler(CommandHandler("calendar", unified_calendar_handler))  # Unified handler
    application.add_handler(CommandHandler("calendar_simple", manager_calendar_simple.simple_calendar_connect))  # Simple method
    application.add_handler(CommandHandler("calendar_instructions", manager_calendar_simple.simple_calendar_connect))  # Alias for simple method
    application.add_handler(CommandHandler("setcalendar", manager_calendar_simple.set_calendar_id))  # Set calendar ID
    application.add_handler(CommandHandler("disconnect_calendar", manager_calendar_simple.disconnect_calendar))  # Disconnect calendar
    application.add_handler(CommandHandler("email", manager_calendar.save_manager_email))
    application.add_handler(check_oauth_status.create_check_oauth_handler())  # Check OAuth status
    
    logger.info("🤖 ✅ ALL HANDLERS ADDED SUCCESSFULLY")
    logger.info(f"🤖 TOTAL HANDLERS: {len(application.handlers[0])}")  # Get first group handlers count
    
    # Error handler already added earlier
    # application.add_error_handler(error_handler)  # Commented out to avoid duplicate
    
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
            # Use manual webhook setup with custom aiohttp server
            webhook_full_url = f"{settings.webhook_url}{settings.webhook_path}"
            logger.info(f"🌐 Starting webhook mode on port {settings.port}")
            logger.info(f"🔗 Webhook URL: {webhook_full_url}")
            
            import asyncio
            from aiohttp import web as aio_web
            
            async def webhook_handler(request):
                """Handle incoming webhook updates."""
                try:
                    logger.info("📥 WEBHOOK: ========== NEW REQUEST ==========")
                    logger.info(f"📥 WEBHOOK: Request method: {request.method}")
                    logger.info(f"📥 WEBHOOK: Request path: {request.path}")
                    logger.info(f"📥 WEBHOOK: Request headers: {dict(request.headers)}")
                    
                    data = await request.json()
                    logger.info(f"📥 WEBHOOK: Raw data: {data}")
                    logger.info(f"📥 WEBHOOK: Data keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
                    
                    update = Update.de_json(data, application.bot)
                    logger.info(f"📥 WEBHOOK: Update object created: {update is not None}")
                    
                    if update:
                        logger.info(f"📥 WEBHOOK: Update ID: {update.update_id}")
                        logger.info(f"📥 WEBHOOK: Processing update type: {type(update).__name__}")
                        
                        if update.message:
                            user = update.message.from_user
                            logger.info(f"📥 WEBHOOK: MESSAGE from user {user.id} (@{user.username})")
                            logger.info(f"📥 WEBHOOK: Message text: '{update.message.text}'")
                            logger.info(f"📥 WEBHOOK: Message chat: {update.message.chat.id}")
                        elif update.callback_query:
                            user = update.callback_query.from_user
                            logger.info(f"📥 WEBHOOK: CALLBACK from user {user.id} (@{user.username})")
                            logger.info(f"📥 WEBHOOK: Callback data: '{update.callback_query.data}'")
                            logger.info(f"📥 WEBHOOK: Callback message: {update.callback_query.message.message_id if update.callback_query.message else 'None'}")
                        else:
                            logger.info(f"📥 WEBHOOK: Other update type: {update}")
                        
                        logger.info("📥 WEBHOOK: Starting application.process_update...")
                        await application.process_update(update)
                        logger.info("📥 WEBHOOK: ✅ Update processed successfully")
                    else:
                        logger.warning("📥 WEBHOOK: ❌ No update object created from data")
                    
                    logger.info("📥 WEBHOOK: Returning 200 response")
                    return aio_web.Response(status=200)
                except Exception as e:
                    logger.error(f"📥 WEBHOOK ERROR: {type(e).__name__}: {e}")
                    logger.error(f"📥 WEBHOOK TRACEBACK: {traceback.format_exc()}")
                    logger.error("📥 WEBHOOK: Returning 500 response")
                    return aio_web.Response(status=500)
            
            async def start_webhook_server():
                """Start combined webhook and health server."""
                app = aio_web.Application()
                
                # Add webhook handler
                app.router.add_post(settings.webhook_path, webhook_handler)
                
                # Add GET handler for webhook diagnostics
                async def webhook_info_handler(request):
                    return aio_web.Response(
                        text="Webhook endpoint is working. Use POST for Telegram updates.",
                        content_type='text/plain'
                    )
                app.router.add_get(settings.webhook_path, webhook_info_handler)
                
                # Add health check handler
                app.router.add_get('/health', health_handler)
                
                # Add OAuth callback handler
                from utils.oauth_handlers import oauth_callback_handler
                app.router.add_get('/oauth/callback', lambda req: oauth_callback_handler(req, application))
                
                # Start server FIRST
                runner = aio_web.AppRunner(app)
                await runner.setup()
                site = aio_web.TCPSite(runner, '0.0.0.0', settings.port)
                await site.start()
                logger.info(f"✅ Webhook server started on port {settings.port}")
                logger.info(f"✅ Health check available at /health")
                
                # Wait a bit for server to be ready
                await asyncio.sleep(2)
                
                # THEN set webhook with Telegram
                await application.bot.set_webhook(
                    url=webhook_full_url,
                    allowed_updates=Update.ALL_TYPES
                )
                logger.info(f"✅ Webhook set: {webhook_full_url}")
                
                # Check webhook info
                try:
                    webhook_info = await application.bot.get_webhook_info()
                    logger.info(f"🔗 WEBHOOK INFO: URL={webhook_info.url}")
                    logger.info(f"🔗 WEBHOOK INFO: Pending updates={webhook_info.pending_update_count}")
                    if webhook_info.last_error_message:
                        logger.error(f"🔗 WEBHOOK ERROR: {webhook_info.last_error_message}")
                    else:
                        logger.info(f"🔗 WEBHOOK STATUS: OK - No errors")
                except Exception as e:
                    logger.error(f"Failed to get webhook info: {e}")
                
                # Initialize application
                await application.initialize()
                await application.start()
                
                # Keep running
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Shutting down...")
                finally:
                    await application.stop()
                    await application.shutdown()
            
            # Run the webhook server
            await start_webhook_server()
            
        else:
            logger.info("🔄 Starting polling mode for development")
            # Polling mode for development
            await application.initialize()
            await application.start()
            
            # Use update queues for polling
            await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            
            try:
                # Keep running
                import asyncio
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
            finally:
                await application.updater.stop()
                await application.stop()  
                await application.shutdown()
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}")
        try:
            scheduler.shutdown()
        except Exception as shutdown_error:
            logger.error(f"❌ Scheduler shutdown error: {shutdown_error}")
        raise

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())