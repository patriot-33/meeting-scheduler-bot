#!/usr/bin/env python3
"""
Локальный запуск бота для разработки
"""
import os
import sys
import logging
import asyncio
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import main

def setup_local_environment():
    """Настройка локального окружения"""
    
    # Загружаем .env файл если существует
    env_file = Path(".env")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Загружены переменные из .env")
    else:
        print("⚠️ Файл .env не найден, используются переменные окружения")
    
    # Проверяем обязательные переменные
    required_vars = ["TELEGRAM_BOT_TOKEN"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
        print("📋 Создайте файл .env на основе .env.local")
        return False
    
    # Устанавливаем режим разработки
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    print("🚀 Локальное окружение настроено")
    return True

def main_local():
    """Главная функция для локального запуска"""
    print("🤖 Запуск Meeting Scheduler Bot (локальная разработка)")
    print("=" * 50)
    
    if not setup_local_environment():
        sys.exit(1)
    
    print("🔧 Режим: Локальная разработка")
    print("📝 Логи: Подробные (DEBUG)")
    print("💾 База данных: SQLite (локальная)")
    print("🌐 Webhook: Отключен (polling mode)")
    print("=" * 50)
    
    try:
        # Запускаем бота
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main_local()