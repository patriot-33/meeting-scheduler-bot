#!/usr/bin/env python3
"""
🤖 TEST BOT LAUNCHER - Запуск бота для тестирования с усиленным логированием
"""

import sys
import os
import logging
from pathlib import Path
import asyncio
from datetime import datetime

# Добавляем src в Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_enhanced_logging():
    """Настройка усиленного логирования для тестирования"""
    
    # Создаем уникальный файл лога для этой сессии
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"test_bot_{timestamp}.log"
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.FileHandler('test_session.log', encoding='utf-8'),  # Общий файл
            logging.StreamHandler(sys.stdout)  # В консоль
        ],
        force=True  # Переопределить существующую конфигурацию
    )
    
    # Настройка уровней для разных модулей
    logging.getLogger('telegram').setLevel(logging.INFO)  # Меньше шума от telegram
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('googleapiclient').setLevel(logging.INFO)
    
    # Наши модули - полная детализация
    logging.getLogger('handlers').setLevel(logging.DEBUG)
    logging.getLogger('services').setLevel(logging.DEBUG)
    logging.getLogger('utils').setLevel(logging.DEBUG)
    logging.getLogger('database').setLevel(logging.DEBUG)
    
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 ТЕСТОВАЯ СЕССИЯ БОТА НАЧИНАЕТСЯ")
    logger.info(f"📋 Логи сохраняются в: {log_filename}")
    logger.info(f"📋 Общий лог: test_session.log")
    logger.info(f"⏰ Время запуска: {datetime.now()}")
    logger.info("="*80)
    
    return log_filename

def check_configuration():
    """Проверка конфигурации перед запуском"""
    logger = logging.getLogger(__name__)
    
    try:
        from config import settings, validate_configuration, print_configuration_summary
        
        logger.info("🔧 Проверка конфигурации...")
        
        # Выводим конфигурацию
        print_configuration_summary()
        
        # Валидация
        is_valid, errors = validate_configuration()
        
        if not is_valid:
            logger.error("❌ ОШИБКИ КОНФИГУРАЦИИ:")
            for error in errors:
                logger.error(f"   - {error}")
            return False
        
        logger.info("✅ Конфигурация валидна")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке конфигурации: {e}")
        return False

def log_system_environment():
    """Логирование информации о системном окружении"""
    logger = logging.getLogger(__name__)
    
    logger.info("🖥️ ИНФОРМАЦИЯ О СИСТЕМЕ:")
    logger.info(f"   Python: {sys.version}")
    logger.info(f"   Platform: {sys.platform}")
    logger.info(f"   Working directory: {os.getcwd()}")
    logger.info(f"   Script path: {__file__}")
    
    # Проверяем основные файлы
    important_files = [
        'src/main.py',
        'src/config.py', 
        'src/database.py',
        'meeting_scheduler.db',
        '.env'
    ]
    
    logger.info("📁 ПРОВЕРКА ФАЙЛОВ:")
    for file_path in important_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            logger.info(f"   ✅ {file_path} ({size} bytes)")
        else:
            logger.info(f"   ❌ {file_path} (не найден)")
    
    # Переменные окружения (безопасно)
    env_vars = [
        'TELEGRAM_BOT_TOKEN',
        'DATABASE_URL', 
        'ENVIRONMENT',
        'DEBUG',
        'GOOGLE_CALENDAR_ENABLED'
    ]
    
    logger.info("🔑 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'TOKEN' in var or 'KEY' in var:
                # Маскируем токены
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                logger.info(f"   {var}: {masked}")
            else:
                logger.info(f"   {var}: {value}")
        else:
            logger.info(f"   {var}: не установлена")

async def run_test_bot():
    """Запуск бота в тестовом режиме"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🤖 ЗАПУСК TELEGRAM БОТА...")
        
        # Импортируем и запускаем main
        from main import main
        
        logger.info("🚀 Запускаем main() функцию...")
        await main()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки (Ctrl+C)")
        logger.info("🛑 Останавливаем бота...")
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА при запуске бота:")
        logger.error(f"   Тип ошибки: {type(e).__name__}")
        logger.error(f"   Сообщение: {str(e)}")
        logger.error(f"   Трейсбек:")
        import traceback
        logger.error(traceback.format_exc())
        raise

def main():
    """Главная функция тестового запуска"""
    print("🛡️ СИСТЕМА ТЕСТИРОВАНИЯ MEETING-SCHEDULER-BOT")
    print("=" * 60)
    
    # Настройка логирования
    log_file = setup_enhanced_logging()
    
    # Логирование системной информации
    log_system_environment()
    
    # Проверка конфигурации
    if not check_configuration():
        print("❌ Ошибки конфигурации. Проверьте логи.")
        sys.exit(1)
    
    print("\n🤖 ЗАПУСК БОТА ДЛЯ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    print(f"📋 Логи: {log_file}")
    print("📋 Общий лог: test_session.log")
    print("🔍 Для остановки нажмите Ctrl+C")
    print("=" * 60)
    
    # Запуск бота
    try:
        asyncio.run(run_test_bot())
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
    finally:
        print(f"\n📋 Проверьте логи в файлах:")
        print(f"   - {log_file}")
        print(f"   - test_session.log")
        print("🏁 Тестовая сессия завершена")

if __name__ == "__main__":
    main()