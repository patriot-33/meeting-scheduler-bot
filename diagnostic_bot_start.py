#!/usr/bin/env python3
"""
🔍 ДИАГНОСТИЧЕСКИЙ СКРИПТ: Тестирование запуска бота
"""

import os
import sys
import logging
import asyncio
from datetime import datetime

# Добавляем src в путь для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Настройка логирования для диагностики
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('diagnostic_run.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_system_state():
    """Логирование состояния системы"""
    logger.info("="*60)
    logger.info("🔍 ДИАГНОСТИЧЕСКИЙ ЗАПУСК MEETING SCHEDULER BOT")
    logger.info("="*60)
    logger.info(f"🕐 Время запуска: {datetime.now()}")
    logger.info(f"📍 Рабочая директория: {os.getcwd()}")
    logger.info(f"🐍 Python версия: {sys.version}")
    logger.info(f"📁 Путь Python: {sys.executable}")
    
def check_environment():
    """Проверка переменных окружения"""
    logger.info("\n📋 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    
    # Критичные переменные
    critical_vars = {
        'TELEGRAM_BOT_TOKEN': 'Токен Telegram бота',
        'DATABASE_URL': 'URL базы данных',
        'ADMIN_TELEGRAM_IDS': 'ID администраторов'
    }
    
    # Опциональные переменные
    optional_vars = {
        'GOOGLE_CALENDAR_ID_1': 'Google Calendar ID 1',
        'GOOGLE_CALENDAR_ID_2': 'Google Calendar ID 2', 
        'GOOGLE_SERVICE_ACCOUNT_JSON': 'Google Service Account JSON',
        'GOOGLE_SERVICE_ACCOUNT_FILE': 'Google Service Account File',
        'TIMEZONE': 'Часовой пояс',
        'LOG_LEVEL': 'Уровень логирования',
        'ENVIRONMENT': 'Окружение'
    }
    
    missing_critical = []
    
    # Проверяем критичные
    for var, desc in critical_vars.items():
        value = os.getenv(var)
        if value:
            # Маскируем чувствительные данные
            if 'TOKEN' in var or 'URL' in var:
                masked = value[:10] + '***' + value[-5:] if len(value) > 15 else '***'
                logger.info(f"   ✅ {var}: {masked} ({desc})")
            else:
                logger.info(f"   ✅ {var}: {value} ({desc})")
        else:
            logger.error(f"   ❌ {var}: НЕ ЗАДАНА! ({desc})")
            missing_critical.append(var)
    
    # Проверяем опциональные
    logger.info("\n📋 ОПЦИОНАЛЬНЫЕ ПЕРЕМЕННЫЕ:")
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            if 'JSON' in var:
                logger.info(f"   ✅ {var}: [JSON данные] ({desc})")
            else:
                logger.info(f"   ✅ {var}: {value} ({desc})")
        else:
            logger.info(f"   ⚪ {var}: не задана ({desc})")
    
    return len(missing_critical) == 0, missing_critical

def test_imports():
    """Тестирование импорта модулей"""
    logger.info("\n📦 ПРОВЕРКА ИМПОРТА МОДУЛЕЙ:")
    
    modules_to_test = [
        ('config', 'Конфигурация'),
        ('database', 'База данных'),
        ('main', 'Главный модуль'),
        ('handlers.common', 'Общие обработчики'),
        ('handlers.registration', 'Регистрация'),
        ('handlers.manager', 'Обработчики менеджера'),
        ('handlers.owner', 'Обработчики владельца'),
        ('services.meeting_service', 'Сервис встреч'),
        ('services.google_calendar', 'Google Calendar'),
        ('utils.scheduler', 'Планировщик')
    ]
    
    import_errors = []
    
    for module_name, desc in modules_to_test:
        try:
            __import__(module_name)
            logger.info(f"   ✅ {module_name}: {desc}")
        except Exception as e:
            logger.error(f"   ❌ {module_name}: {type(e).__name__}: {e}")
            import_errors.append((module_name, str(e)))
    
    return len(import_errors) == 0, import_errors

def test_config():
    """Тестирование конфигурации"""
    logger.info("\n⚙️ ПРОВЕРКА КОНФИГУРАЦИИ:")
    
    try:
        from config import settings
        
        # Проверяем базовые настройки
        logger.info(f"   📱 Telegram Token: {'✅ Задан' if settings.telegram_bot_token else '❌ НЕ ЗАДАН'}")
        logger.info(f"   🗄️ Database URL: {'✅ Задан' if settings.database_url else '❌ НЕ ЗАДАН'}")
        logger.info(f"   👤 Admin IDs: {settings.admin_ids_list}")
        logger.info(f"   🌍 Timezone: {settings.timezone}")
        logger.info(f"   📊 Log Level: {settings.log_level}")
        logger.info(f"   🏭 Environment: {settings.environment}")
        logger.info(f"   🗓️ Google Calendar Enabled: {settings.google_calendar_enabled}")
        logger.info(f"   🔄 Fallback Mode: {settings.fallback_mode}")
        
        # Валидация конфигурации
        errors = []
        if not settings.telegram_bot_token:
            errors.append("TELEGRAM_BOT_TOKEN не задан")
        if not settings.admin_ids_list:
            errors.append("ADMIN_TELEGRAM_IDS не задан или пустой")
            
        if errors:
            for error in errors:
                logger.error(f"   ❌ {error}")
            return False, errors
        else:
            logger.info("   ✅ Конфигурация валидна")
            return True, []
            
    except Exception as e:
        logger.error(f"   ❌ Ошибка загрузки конфигурации: {type(e).__name__}: {e}")
        return False, [str(e)]

def test_database_connection():
    """Тестирование подключения к БД"""
    logger.info("\n🗄️ ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ:")
    
    try:
        from database import engine, get_db, Base
        from sqlalchemy import text
        
        # Тестируем подключение
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("   ✅ Подключение к БД успешно")
            
            # Проверяем таблицы
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            logger.info(f"   📊 Найдено таблиц: {len(tables)}")
            for table in tables:
                logger.info(f"      - {table}")
                
        return True, []
        
    except Exception as e:
        logger.error(f"   ❌ Ошибка подключения к БД: {type(e).__name__}: {e}")
        return False, [str(e)]

async def test_bot_startup():
    """Тестирование запуска бота"""
    logger.info("\n🤖 ТЕСТИРОВАНИЕ ЗАПУСКА БОТА:")
    
    try:
        from telegram import Bot
        from config import settings
        
        if not settings.telegram_bot_token:
            logger.error("   ❌ Токен бота не задан!")
            return False, ["Токен бота не задан"]
        
        # Создаем экземпляр бота
        bot = Bot(token=settings.telegram_bot_token)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"   ✅ Бот подключен: @{bot_info.username}")
        logger.info(f"      - ID: {bot_info.id}")
        logger.info(f"      - Имя: {bot_info.first_name}")
        logger.info(f"      - Can join groups: {bot_info.can_join_groups}")
        logger.info(f"      - Can read all messages: {bot_info.can_read_all_group_messages}")
        
        # Проверяем webhook
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            logger.info(f"   🔗 Webhook: {webhook_info.url}")
        else:
            logger.info("   🔗 Webhook: не установлен (polling mode)")
            
        await bot.close()
        return True, []
        
    except Exception as e:
        logger.error(f"   ❌ Ошибка запуска бота: {type(e).__name__}: {e}")
        return False, [str(e)]

async def main():
    """Главная функция диагностики"""
    log_system_state()
    
    results = []
    
    # 1. Проверка окружения
    success, missing = check_environment()
    results.append(("Environment Variables", success, missing))
    
    # 2. Проверка импортов
    success, errors = test_imports()
    results.append(("Module Imports", success, errors))
    
    # 3. Проверка конфигурации
    success, errors = test_config()
    results.append(("Configuration", success, errors))
    
    # 4. Проверка БД
    success, errors = test_database_connection()
    results.append(("Database Connection", success, errors))
    
    # 5. Проверка бота
    success, errors = await test_bot_startup()
    results.append(("Bot Startup", success, errors))
    
    # Итоговый отчет
    logger.info("\n" + "="*60)
    logger.info("📊 ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ:")
    logger.info("="*60)
    
    total_success = sum(1 for _, success, _ in results if success)
    
    for test_name, success, errors in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if errors and not success:
            for error in errors:
                logger.info(f"   - {error}")
    
    logger.info(f"\n🎯 Результат: {total_success}/{len(results)} тестов пройдено")
    
    if total_success == len(results):
        logger.info("\n✅ БОТ ГОТОВ К ЗАПУСКУ!")
        logger.info("Запустите бота командой: python src/main.py")
    else:
        logger.error("\n❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        logger.error("Исправьте ошибки выше перед запуском бота.")
        
        # Рекомендации
        logger.info("\n💡 РЕКОМЕНДАЦИИ:")
        
        # Проверяем наличие критичных переменных
        env_test = next((r for r in results if r[0] == "Environment Variables"), None)
        if env_test and not env_test[1]:
            logger.info("1. Создайте файл .env на основе .env.example:")
            logger.info("   cp .env.example .env")
            logger.info("2. Заполните обязательные переменные в .env файле")
            
        # Проверяем токен бота
        bot_test = next((r for r in results if r[0] == "Bot Startup"), None)
        if bot_test and not bot_test[1]:
            logger.info("3. Проверьте правильность TELEGRAM_BOT_TOKEN")
            logger.info("4. Убедитесь, что бот создан через @BotFather")
    
    logger.info("\n📝 Логи сохранены в: diagnostic_run.log")
    
    return total_success == len(results)

if __name__ == "__main__":
    # Запускаем диагностику
    success = asyncio.run(main())
    sys.exit(0 if success else 1)