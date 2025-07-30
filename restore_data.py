#!/usr/bin/env python3
"""
Data Restore Script for Meeting Scheduler Bot
Восстанавливает данные из backup после деплоя
"""

import sys
import json
import os
from datetime import datetime

# Добавляем src в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def restore_data(backup_file):
    """Восстановление данных из JSON backup"""
    
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    try:
        from database import get_db, User, OwnerAvailability, Meeting, Reminder
        from database import UserRole, UserStatus, MeetingStatus, Department
        from sqlalchemy.exc import IntegrityError
        
        # Загружаем backup
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
            
        print(f"📂 Loading backup from {backup_data.get('backup_timestamp', 'unknown time')}")
        
        with get_db() as db:
            restored = {'users': 0, 'slots': 0, 'meetings': 0, 'reminders': 0}
            
            # Восстанавливаем пользователей
            for user_data in backup_data.get('users', []):
                try:
                    # Проверяем, не существует ли уже пользователь
                    existing = db.query(User).filter_by(telegram_id=user_data['telegram_id']).first()
                    if existing:
                        print(f"⚠️ User {user_data['telegram_id']} already exists, skipping")
                        continue
                        
                    user = User(
                        telegram_id=user_data['telegram_id'],
                        telegram_username=user_data.get('telegram_username'),
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],  
                        email=user_data.get('email'),
                        department=Department(user_data['department']),
                        role=UserRole(user_data['role']) if user_data['role'] else UserRole.PENDING,
                        status=UserStatus(user_data['status']) if user_data['status'] else UserStatus.ACTIVE
                    )
                    db.add(user)
                    restored['users'] += 1
                except Exception as e:
                    print(f"⚠️ Failed to restore user {user_data.get('telegram_id', 'unknown')}: {e}")
            
            # Коммитим пользователей сначала, чтобы получить их ID
            try:
                db.commit()
            except IntegrityError as e:
                print(f"⚠️ Some users already exist: {e}")
                db.rollback()
                
            # Восстанавливаем слоты доступности
            for slot_data in backup_data.get('owner_availability', []):
                try:
                    # Находим пользователя по telegram_id из backup
                    owner = db.query(User).filter_by(telegram_id=slot_data['owner_id']).first()
                    if not owner:
                        print(f"⚠️ Owner not found for slot, skipping")
                        continue
                        
                    slot = OwnerAvailability(
                        owner_id=owner.id,
                        day_of_week=slot_data['day_of_week'],
                        time_slot=slot_data['time_slot'],
                        is_active=slot_data.get('is_active', True)
                    )
                    db.add(slot)
                    restored['slots'] += 1
                except Exception as e:
                    print(f"⚠️ Failed to restore slot: {e}")
            
            # Восстанавливаем встречи
            for meeting_data in backup_data.get('meetings', []):
                try:
                    manager = db.query(User).filter_by(telegram_id=meeting_data['manager_id']).first()
                    if not manager:
                        continue
                        
                    meeting = Meeting(
                        manager_id=manager.id,
                        scheduled_time=datetime.fromisoformat(meeting_data['scheduled_time']),
                        google_event_id=meeting_data.get('google_event_id'),
                        google_meet_link=meeting_data.get('google_meet_link'),
                        status=MeetingStatus(meeting_data['status']) if meeting_data['status'] else MeetingStatus.SCHEDULED
                    )
                    db.add(meeting)
                    restored['meetings'] += 1
                except Exception as e:
                    print(f"⚠️ Failed to restore meeting: {e}")
            
            # Коммитим все изменения
            db.commit()
            
            print(f"✅ Restore completed:")
            for table, count in restored.items():
                if count > 0:
                    print(f"  - {table}: {count} records restored")
                    
            return True
            
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python restore_data.py <backup_file.json>")
        sys.exit(1)
        
    restore_data(sys.argv[1])
