#!/usr/bin/env python3
"""
Инструменты для разработки
"""
import os
import sys
import subprocess
import json
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

def restart_bot():
    """Перезапуск бота"""
    print("🔄 Перезапуск бота...")
    
    # Ищем процесс бота
    try:
        result = subprocess.run(['pgrep', '-f', 'run_local.py'], 
                              capture_output=True, text=True)
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"🛑 Остановка процесса {pid}")
                    subprocess.run(['kill', pid])
        else:
            print("ℹ️ Бот не запущен")
    except Exception as e:
        print(f"⚠️ Ошибка остановки: {e}")
    
    # Запускаем бота
    print("🚀 Запуск бота...")
    subprocess.Popen(['python3', 'run_local.py'])

def check_db():
    """Проверка базы данных"""
    print("🔍 Проверка базы данных...")
    
    try:
        from src.database import SessionLocal, User, Meeting
        from sqlalchemy import text
        
        with SessionLocal() as db:
            # Проверяем таблицы
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Таблицы: {', '.join(tables)}")
            
            # Проверяем пользователей
            users_count = db.query(User).count()
            print(f"👥 Пользователей: {users_count}")
            
            # Проверяем встречи  
            meetings_count = db.query(Meeting).count()
            print(f"🤝 Встреч: {meetings_count}")
            
            # Проверяем структуру таблицы meetings
            result = db.execute(text("PRAGMA table_info(meetings)"))
            columns = [row[1] for row in result.fetchall()]
            print(f"📊 Колонки meetings: {', '.join(columns)}")
            
            if 'google_calendar_id' in columns:
                print("✅ Колонка google_calendar_id присутствует")
            else:
                print("❌ Колонка google_calendar_id отсутствует")
                
    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")

def test_config():
    """Тестирование конфигурации"""
    print("🔧 Тестирование конфигурации...")
    
    try:
        from src.config import settings
        
        print(f"🤖 Telegram Token: {'✅ Установлен' if settings.telegram_bot_token else '❌ Не установлен'}")
        print(f"💾 Database URL: {settings.database_url}")
        print(f"🔍 Debug: {settings.debug}")
        print(f"📝 Log Level: {settings.log_level}")
        
        # Google Calendar
        has_service_account = bool(settings.google_service_account_json)
        has_oauth_client = bool(settings.google_oauth_client_json)
        
        print(f"🔑 Google Service Account: {'✅' if has_service_account else '❌'}")
        print(f"🔐 Google OAuth Client: {'✅' if has_oauth_client else '❌'}")
        
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")

def show_status():
    """Показать статус системы"""
    print("📊 Статус системы:")
    print("=" * 30)
    
    # Проверяем процесс бота
    try:
        result = subprocess.run(['pgrep', '-f', 'run_local.py'], 
                              capture_output=True, text=True)
        if result.stdout:
            print("🤖 Бот: ✅ Запущен")
        else:
            print("🤖 Бот: ❌ Остановлен")
    except:
        print("🤖 Бот: ❓ Неизвестно")
    
    # Проверяем файлы
    files_to_check = ['.env', 'bot.log', 'meeting_scheduler.db']
    for file in files_to_check:
        path = Path(file)
        status = "✅" if path.exists() else "❌"
        size = f" ({path.stat().st_size} bytes)" if path.exists() else ""
        print(f"📄 {file}: {status}{size}")

def main():
    """Главное меню инструментов разработки"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Инструменты разработки")
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команды
    subparsers.add_parser('restart', help='Перезапустить бота')
    subparsers.add_parser('check-db', help='Проверить базу данных')
    subparsers.add_parser('test-config', help='Тестировать конфигурацию')
    subparsers.add_parser('status', help='Показать статус системы')
    
    args = parser.parse_args()
    
    if args.command == 'restart':
        restart_bot()
    elif args.command == 'check-db':
        check_db()
    elif args.command == 'test-config':
        test_config()
    elif args.command == 'status':
        show_status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()