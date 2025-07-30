#!/usr/bin/env python3
"""
Скрипт для проверки и восстановления слотов владельцев после деплоя
"""
import logging
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import settings
from src.database import get_db, User, OwnerAvailability, UserRole, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_fix_slots():
    """Проверить и исправить проблемы со слотами владельцев"""
    try:
        logger.info("🔍 Проверка состояния базы данных после деплоя...")
        
        # Инициализируем базу данных
        init_db()
        
        with get_db() as db:
            # 1. Проверяем владельцев
            owners = db.query(User).filter(User.role == UserRole.OWNER).all()
            logger.info(f"👑 Найдено владельцев: {len(owners)}")
            
            for owner in owners:
                logger.info(f"   • {owner.first_name} {owner.last_name} (ID: {owner.id}, Telegram: {owner.telegram_id})")
            
            # 2. Проверяем существующие слоты
            all_slots = db.query(OwnerAvailability).all()
            logger.info(f"📅 Всего слотов в БД: {len(all_slots)}")
            
            # 3. Группируем слоты по владельцам
            owner_slots = {}
            for slot in all_slots:
                if slot.owner_id not in owner_slots:
                    owner_slots[slot.owner_id] = []
                owner_slots[slot.owner_id].append(slot)
            
            # 4. Показываем текущие слоты
            for owner in owners:
                slots = owner_slots.get(owner.id, [])
                logger.info(f"   {owner.first_name}: {len(slots)} слотов")
                
                # Группируем по дням
                days_slots = {}
                for slot in slots:
                    if slot.day_of_week not in days_slots:
                        days_slots[slot.day_of_week] = []
                    days_slots[slot.day_of_week].append(slot.time_slot)
                
                if days_slots:
                    from src.services.owner_service import WEEKDAYS
                    for day_idx, time_slots in days_slots.items():
                        day_name = WEEKDAYS[day_idx] if 0 <= day_idx < len(WEEKDAYS) else f"День {day_idx}"
                        logger.info(f"     - {day_name}: {', '.join(sorted(time_slots))}")
                else:
                    logger.warning(f"     ⚠️ У {owner.first_name} нет настроенных слотов!")
            
            # 5. Проверяем целостность данных
            logger.info("🔧 Проверка целостности данных...")
            
            # Проверяем orphaned слоты (слоты без владельца)
            orphaned_slots = db.query(OwnerAvailability).filter(
                ~OwnerAvailability.owner_id.in_([owner.id for owner in owners])
            ).all()
            
            if orphaned_slots:
                logger.warning(f"⚠️ Найдено {len(orphaned_slots)} слотов без владельца")
                for slot in orphaned_slots:
                    logger.warning(f"   - Слот ID {slot.id} для несуществующего владельца {slot.owner_id}")
                
                # Удаляем orphaned слоты
                for slot in orphaned_slots:
                    db.delete(slot)
                db.commit()
                logger.info("✅ Удалены слоты без владельца")
            
            # 6. Проверяем неактивные слоты
            inactive_slots = db.query(OwnerAvailability).filter(
                OwnerAvailability.is_active == False
            ).all()
            
            if inactive_slots:
                logger.info(f"📋 Найдено {len(inactive_slots)} неактивных слотов")
                
                # Можно их активировать обратно если нужно
                # for slot in inactive_slots:
                #     slot.is_active = True
                # db.commit()
            
            # 7. Создаем базовые слоты если их совсем нет
            if len(all_slots) == 0 and len(owners) > 0:
                logger.info("🔄 Создание базовых слотов для владельцев...")
                
                # Базовые слоты: будние дни с 14:00 до 17:00
                base_slots = ["14:00", "15:00", "16:00", "17:00"]
                weekdays = [0, 1, 2, 3, 4]  # Пн-Пт
                
                for owner in owners:
                    logger.info(f"   Создание слотов для {owner.first_name}...")
                    for day in weekdays:
                        for time_slot in base_slots:
                            slot = OwnerAvailability(
                                owner_id=owner.id,
                                day_of_week=day,
                                time_slot=time_slot,
                                is_active=True
                            )
                            db.add(slot)
                    
                db.commit()
                logger.info("✅ Созданы базовые слоты для всех владельцев")
        
        logger.info("✅ Проверка завершена успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке слотов: {e}")
        raise

def backup_slots():
    """Создать резервную копию текущих слотов"""
    try:
        logger.info("💾 Создание резервной копии слотов...")
        
        with get_db() as db:
            slots = db.query(OwnerAvailability).all()
            
            backup_data = []
            for slot in slots:
                backup_data.append({
                    'owner_id': slot.owner_id,
                    'day_of_week': slot.day_of_week,
                    'time_slot': slot.time_slot,
                    'is_active': slot.is_active
                })
            
            # Сохраняем в файл
            import json
            with open('slots_backup.json', 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Резервная копия сохранена: {len(backup_data)} слотов в slots_backup.json")
    
    except Exception as e:
        logger.error(f"❌ Ошибка создания резервной копии: {e}")

def restore_slots_from_backup():
    """Восстановить слоты из резервной копии"""
    try:
        import json
        
        if not os.path.exists('slots_backup.json'):
            logger.error("❌ Файл резервной копии slots_backup.json не найден")
            return
        
        logger.info("🔄 Восстановление слотов из резервной копии...")
        
        with open('slots_backup.json', 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        with get_db() as db:
            # Удаляем существующие слоты
            db.query(OwnerAvailability).delete()
            
            # Восстанавливаем из копии
            restored = 0
            for slot_data in backup_data:
                slot = OwnerAvailability(
                    owner_id=slot_data['owner_id'],
                    day_of_week=slot_data['day_of_week'],
                    time_slot=slot_data['time_slot'],
                    is_active=slot_data['is_active']
                )
                db.add(slot)
                restored += 1
            
            db.commit()
            logger.info(f"✅ Восстановлено {restored} слотов из резервной копии")
    
    except Exception as e:
        logger.error(f"❌ Ошибка восстановления: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Управление слотами владельцев')
    parser.add_argument('--check', action='store_true', help='Проверить состояние слотов')
    parser.add_argument('--backup', action='store_true', help='Создать резервную копию')
    parser.add_argument('--restore', action='store_true', help='Восстановить из резервной копии')
    
    args = parser.parse_args()
    
    if args.backup:
        backup_slots()
    elif args.restore:
        restore_slots_from_backup()
    elif args.check:
        check_and_fix_slots()
    else:
        # По умолчанию - проверка
        check_and_fix_slots()