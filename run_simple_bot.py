#!/usr/bin/env python3
"""
Упрощенный запуск бота без scheduler для тестирования
"""
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

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: Update, context):
    """Обработчик ошибок."""
    logger.error(f"Ошибка: {context.error}")
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла техническая ошибка. Попробуйте позже."
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

async def main():
    """Запуск бота."""
    logger.info("🚀 Запуск упрощенной версии Meeting Scheduler Bot...")
    
    # Инициализация БД
    try:
        init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return
    
    # Создание приложения
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Добавление обработчиков
    application.add_handler(CommandHandler("start", common.start_command))
    application.add_handler(CommandHandler("help", common.help_command))
    application.add_handler(CommandHandler("cancel", common.cancel_command))
    
    # Регистрация
    application.add_handler(registration.get_registration_handler())
    
    # Админские команды
    application.add_handler(CommandHandler("admin", admin.admin_menu))
    application.add_handler(CommandHandler("pending", admin.show_pending_users))
    application.add_handler(CommandHandler("users", admin.list_users))
    application.add_handler(CommandHandler("stats", admin.show_statistics))
    
    # Команды менеджеров
    application.add_handler(CommandHandler("schedule", manager.show_available_slots))
    application.add_handler(CommandHandler("my_meetings", manager.show_my_meetings))
    application.add_handler(CommandHandler("profile", manager.show_profile))
    application.add_handler(CommandHandler("vacation", manager.set_vacation))
    application.add_handler(CommandHandler("sick", manager.set_sick_leave))
    application.add_handler(CommandHandler("trip", manager.set_business_trip))
    application.add_handler(CommandHandler("active", manager.set_active))
    
    # Callback обработчики
    application.add_handler(CallbackQueryHandler(admin.handle_admin_callback, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(manager.handle_booking_callback, pattern="^book_"))
    application.add_handler(CallbackQueryHandler(manager.handle_cancel_callback, pattern="^cancel_"))
    application.add_handler(CallbackQueryHandler(common.handle_navigation_callback, pattern="^nav_"))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запуск в режиме polling
    logger.info("🔄 Запуск в режиме polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    # Отправляем тестовое сообщение админу
    try:
        await application.bot.send_message(
            chat_id=99006770,
            text="✅ Бот запущен локально!\n\nТеперь можете тестировать команды:\n/start\n/help\n/admin"
        )
        logger.info("✅ Тестовое сообщение отправлено")
    except Exception as e:
        logger.error(f"❌ Не удалось отправить тестовое сообщение: {e}")
    
    # Ожидание
    logger.info("🤖 Бот работает. Нажмите Ctrl+C для остановки.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Остановка бота...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())