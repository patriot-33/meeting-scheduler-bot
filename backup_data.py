#!/usr/bin/env python3
"""
Data Backup Script for Meeting Scheduler Bot
Экспортирует критические данные перед деплоем
"""

import sys
import json
import sqlite3
from datetime import datetime

def backup_data():
    """Экспорт данных из SQLite в JSON"""
    
    db_path = 'test.db'  # Will use database from current directory
    backup_data = {
        'backup_timestamp': datetime.now().isoformat(),
        'users': [],
        'owner_availability': [],
        'meetings': [],
        'reminders': []
    }
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Позволяет получать результаты как dict
        cursor = conn.cursor()
        
        # Экспорт пользователей
        cursor.execute("SELECT * FROM users")
        backup_data['users'] = [dict(row) for row in cursor.fetchall()]
        
        # Экспорт доступности владельцев
        cursor.execute("SELECT * FROM owner_availability")
        backup_data['owner_availability'] = [dict(row) for row in cursor.fetchall()]
        
        # Экспорт встреч
        cursor.execute("SELECT * FROM meetings")
        backup_data['meetings'] = [dict(row) for row in cursor.fetchall()]
        
        # Экспорт напоминаний
        cursor.execute("SELECT * FROM reminders")
        backup_data['reminders'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Сохраняем backup
        backup_filename = f'data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
        print(f"✅ Data backed up to {backup_filename}")
        
        # Показываем статистику
        total_records = sum(len(backup_data[key]) for key in ['users', 'owner_availability', 'meetings', 'reminders'])
        print(f"📊 Backed up {total_records} total records:")
        for table, records in backup_data.items():
            if table != 'backup_timestamp' and records:
                print(f"  - {table}: {len(records)} records")
                
        return backup_filename
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

if __name__ == "__main__":
    backup_data()
