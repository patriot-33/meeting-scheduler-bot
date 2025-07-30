#!/usr/bin/env python3
"""
Auto Restore Script - автоматически восстанавливает данные при деплое
Запускается автоматически после инициализации базы данных
"""

import os
import sys
import json
import glob
from datetime import datetime

# Добавляем src в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def find_latest_backup():
    """Находит самый свежий backup файл"""
    backup_patterns = [
        'data_backup_*.json',
        'src/data_backup_*.json',
        '*/data_backup_*.json'
    ]
    
    backup_files = []
    for pattern in backup_patterns:
        backup_files.extend(glob.glob(pattern))
    
    if not backup_files:
        print("❌ No backup files found")
        return None
    
    # Сортируем по дате в имени файла (самый новый первый)
    backup_files.sort(reverse=True)
    latest_backup = backup_files[0]
    
    print(f"📂 Found latest backup: {latest_backup}")
    return latest_backup

def check_if_data_exists():
    """Проверяет, есть ли уже данные в базе"""
    try:
        from database import get_db, User
        
        with get_db() as db:
            user_count = db.query(User).count()
            return user_count > 0
            
    except Exception as e:
        print(f"⚠️ Cannot check existing data: {e}")
        return False

def auto_restore():
    """Автоматическое восстановление данных"""
    print("🔄 Auto Restore: Checking if data restore is needed...")
    
    # Проверяем, есть ли уже данные
    if check_if_data_exists():
        print("✅ Data already exists in database, skipping restore")
        return True
    
    # Ищем backup файл
    backup_file = find_latest_backup()
    if not backup_file:
        print("ℹ️ No backup file found, starting with empty database")
        return True
    
    # Восстанавливаем данные
    print(f"🔄 Restoring data from {backup_file}...")
    
    try:
        # Импортируем restore функцию
        sys.path.append('.')
        from restore_data import restore_data
        
        success = restore_data(backup_file)
        
        if success:
            print("✅ Auto restore completed successfully!")
            return True
        else:
            print("❌ Auto restore failed")
            return False
            
    except Exception as e:
        print(f"❌ Auto restore error: {e}")
        return False

if __name__ == "__main__":
    auto_restore()