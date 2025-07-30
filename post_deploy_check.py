#!/usr/bin/env python3
"""
Скрипт для автоматической проверки после деплоя
Запускается автоматически после успешного деплоя на Render.com
"""
import logging
import sys
import os
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import settings
from src.database import get_db, User, OwnerAvailability, UserRole, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def post_deploy_check():
    """Полная проверка после деплоя"""
    logger.info("🚀 Начинаем проверку после деплоя...")
    
    try:
        # 1. Проверяем подключение к базе данных
        logger.info("1. Проверка подключения к базе данных...")
        init_db()
        logger.info("✅ База данных инициализирована")
        
        # 2. Проверяем владельцев
        logger.info("2. Проверка владельцев бизнеса...")
        with get_db() as db:
            owners = db.query(User).filter(User.role == UserRole.OWNER).all()
            logger.info(f"✅ Найдено владельцев: {len(owners)}")
            
            for owner in owners:
                logger.info(f"   • {owner.first_name} {owner.last_name} (Telegram: {owner.telegram_id})")
        
        # 3. Проверяем слоты
        logger.info("3. Проверка временных слотов...")
        with get_db() as db:
            slots = db.query(OwnerAvailability).filter(OwnerAvailability.is_active == True).all()
            logger.info(f"📅 Активных слотов: {len(slots)}")
            
            # Группируем по владельцам
            owner_slots = {}
            for slot in slots:
                if slot.owner_id not in owner_slots:
                    owner_slots[slot.owner_id] = []
                owner_slots[slot.owner_id].append(slot)
            
            # Проверяем каждого владельца
            for owner in owners:
                owner_slot_count = len(owner_slots.get(owner.id, []))
                if owner_slot_count == 0:
                    logger.warning(f"⚠️ У {owner.first_name} нет активных слотов!")
                    
                    # Создаем базовые слоты
                    logger.info(f"🔄 Создание базовых слотов для {owner.first_name}...")
                    create_default_slots_for_owner(db, owner.id)
                else:
                    logger.info(f"   • {owner.first_name}: {owner_slot_count} слотов")
        
        # 4. Проверяем Google Calendar конфигурацию
        logger.info("4. Проверка Google Calendar конфигурации...")
        if settings.google_calendar_id_1 and settings.google_calendar_id_2:
            logger.info("✅ Google Calendar ID настроены")
        else:
            logger.warning("⚠️ Google Calendar ID не настроены")
        
        if os.path.exists(settings.google_service_account_file):
            logger.info("✅ Google Service Account файл найден")
        else:
            logger.warning(f"⚠️ Google Service Account файл не найден: {settings.google_service_account_file}")
        
        # 5. Создаем отчет о состоянии
        logger.info("5. Создание отчета о состоянии...")
        create_health_report()
        
        logger.info("🎉 Проверка после деплоя завершена успешно!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке после деплоя: {e}")
        return False

def create_default_slots_for_owner(db, owner_id):
    """Создать базовые слоты для владельца"""
    try:
        # Базовые слоты: будние дни 14:00-17:00
        base_slots = ["14:00", "15:00", "16:00", "17:00"]
        weekdays = [0, 1, 2, 3, 4]  # Пн-Пт
        
        created_count = 0
        for day in weekdays:
            for time_slot in base_slots:
                # Проверяем, не существует ли уже такой слот
                existing = db.query(OwnerAvailability).filter(
                    OwnerAvailability.owner_id == owner_id,
                    OwnerAvailability.day_of_week == day,
                    OwnerAvailability.time_slot == time_slot
                ).first()
                
                if not existing:
                    slot = OwnerAvailability(
                        owner_id=owner_id,
                        day_of_week=day,
                        time_slot=time_slot,
                        is_active=True
                    )
                    db.add(slot)
                    created_count += 1
        
        db.commit()
        logger.info(f"✅ Создано {created_count} базовых слотов")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания базовых слотов: {e}")
        db.rollback()

def create_health_report():
    """Создать отчет о состоянии системы"""
    try:
        report = {
            "timestamp": datetime.now().isoformat(),
            "database": {"status": "connected"},
            "owners": [],
            "slots": {"total": 0, "by_owner": {}},
            "config": {
                "google_calendar_configured": bool(settings.google_calendar_id_1 and settings.google_calendar_id_2),
                "service_account_file_exists": os.path.exists(settings.google_service_account_file),
                "timezone": settings.timezone
            }
        }
        
        with get_db() as db:
            # Владельцы
            owners = db.query(User).filter(User.role == UserRole.OWNER).all()
            for owner in owners:
                report["owners"].append({
                    "id": owner.id,
                    "name": f"{owner.first_name} {owner.last_name}",
                    "telegram_id": owner.telegram_id
                })
            
            # Слоты
            slots = db.query(OwnerAvailability).filter(OwnerAvailability.is_active == True).all()
            report["slots"]["total"] = len(slots)
            
            for owner in owners:
                owner_slots = [s for s in slots if s.owner_id == owner.id]
                report["slots"]["by_owner"][owner.id] = len(owner_slots)
        
        # Сохраняем отчет
        with open('health_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ Отчет о состоянии сохранен в health_report.json")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания отчета: {e}")

if __name__ == '__main__':
    success = post_deploy_check()
    sys.exit(0 if success else 1)