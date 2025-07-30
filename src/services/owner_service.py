"""
Сервис управления владельцами бизнеса
"""
import logging
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import get_db, User, UserRole, OwnerAvailability, OwnerBlockedTime
from config import settings

logger = logging.getLogger(__name__)

WEEKDAYS = [
    "Понедельник", "Вторник", "Среда", "Четверг", 
    "Пятница", "Суббота", "Воскресенье"
]

TIME_SLOTS = [
    "09:00", "10:00", "11:00", "12:00", "13:00", 
    "14:00", "15:00", "16:00", "17:00", "18:00"
]

class OwnerService:
    
    @staticmethod
    def is_owner(user_id: int) -> bool:
        """Проверка, является ли пользователь владельцем"""
        return user_id in settings.admin_ids_list
    
    @staticmethod
    def get_owner_by_telegram_id(telegram_id: int) -> Optional[User]:
        """Получить владельца по Telegram ID"""
        with get_db() as db:
            return db.query(User).filter(
                and_(User.telegram_id == telegram_id, User.role == UserRole.OWNER)
            ).first()
    
    @staticmethod
    def get_all_owners() -> List[User]:
        """Получить всех владельцев"""
        with get_db() as db:
            return db.query(User).filter(User.role == UserRole.OWNER).all()
    
    @staticmethod
    def get_owner_availability(owner_id: int) -> List[OwnerAvailability]:
        """Получить доступность владельца по дням недели"""
        with get_db() as db:
            return db.query(OwnerAvailability).filter(
                and_(
                    OwnerAvailability.owner_id == owner_id,
                    OwnerAvailability.is_active == True
                )
            ).order_by(OwnerAvailability.day_of_week).all()
    
    @staticmethod
    def set_owner_time_slots(owner_id: int, day_of_week: int, time_slots: list) -> bool:
        """Установить временные слоты владельца на конкретный день"""
        try:
            with get_db() as db:
                # Удаляем старые слоты для этого дня
                db.query(OwnerAvailability).filter(
                    and_(
                        OwnerAvailability.owner_id == owner_id,
                        OwnerAvailability.day_of_week == day_of_week
                    )
                ).delete()
                
                # Добавляем новые слоты
                for time_slot in time_slots:
                    availability = OwnerAvailability(
                        owner_id=owner_id,
                        day_of_week=day_of_week,
                        time_slot=time_slot,
                        is_active=True
                    )
                    db.add(availability)
                
                db.commit()
                
                slots_str = ", ".join(time_slots)
                logger.info(f"✅ Установлены временные слоты для владельца {owner_id}: {WEEKDAYS[day_of_week]} - {slots_str}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка установки временных слотов: {e}")
            return False
    
    @staticmethod
    def add_owner_time_slot(owner_id: int, day_of_week: int, time_slot: str) -> bool:
        """Добавить один временной слот владельцу на конкретный день"""
        try:
            with get_db() as db:
                # Проверяем, не существует ли уже такой слот
                existing = db.query(OwnerAvailability).filter(
                    and_(
                        OwnerAvailability.owner_id == owner_id,
                        OwnerAvailability.day_of_week == day_of_week,
                        OwnerAvailability.time_slot == time_slot,
                        OwnerAvailability.is_active == True
                    )
                ).first()
                
                if existing:
                    logger.info(f"⚠️ Слот {time_slot} уже существует для {WEEKDAYS[day_of_week]}")
                    return False
                
                # Добавляем новый слот
                availability = OwnerAvailability(
                    owner_id=owner_id,
                    day_of_week=day_of_week,
                    time_slot=time_slot,
                    is_active=True
                )
                db.add(availability)
                db.commit()
                
                logger.info(f"✅ Добавлен слот для владельца {owner_id}: {WEEKDAYS[day_of_week]} {time_slot}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления слота: {e}")
            return False
    
    @staticmethod
    def remove_owner_time_slot(owner_id: int, day_of_week: int, time_slot: str) -> bool:
        """Удалить конкретный временной слот владельца"""
        try:
            with get_db() as db:
                deleted = db.query(OwnerAvailability).filter(
                    and_(
                        OwnerAvailability.owner_id == owner_id,
                        OwnerAvailability.day_of_week == day_of_week,
                        OwnerAvailability.time_slot == time_slot
                    )
                ).delete()
                db.commit()
                
                if deleted:
                    logger.info(f"✅ Удален слот для владельца {owner_id}: {WEEKDAYS[day_of_week]} {time_slot}")
                    return True
                else:
                    logger.info(f"⚠️ Слот {time_slot} не найден для {WEEKDAYS[day_of_week]}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка удаления слота: {e}")
            return False
    
    @staticmethod
    def remove_all_day_slots(owner_id: int, day_of_week: int) -> bool:
        """Удалить все временные слоты владельца на конкретный день"""
        try:
            with get_db() as db:
                deleted = db.query(OwnerAvailability).filter(
                    and_(
                        OwnerAvailability.owner_id == owner_id,
                        OwnerAvailability.day_of_week == day_of_week
                    )
                ).delete()
                db.commit()
                
                logger.info(f"✅ Удалены все слоты для владельца {owner_id}: {WEEKDAYS[day_of_week]} (удалено: {deleted})")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка удаления слотов дня: {e}")
            return False
    
    @staticmethod
    def get_owner_time_slots(owner_id: int, day_of_week: int) -> List[str]:
        """Получить все временные слоты владельца на конкретный день"""
        try:
            with get_db() as db:
                slots = db.query(OwnerAvailability.time_slot).filter(
                    and_(
                        OwnerAvailability.owner_id == owner_id,
                        OwnerAvailability.day_of_week == day_of_week,
                        OwnerAvailability.is_active == True
                    )
                ).order_by(OwnerAvailability.time_slot).all()
                
                return [slot[0] for slot in slots]
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения слотов: {e}")
            return []
    
    @staticmethod
    def block_owner_time(owner_id: int, blocked_from: datetime, blocked_to: datetime, reason: str = "") -> bool:
        """Заблокировать время владельца"""
        try:
            with get_db() as db:
                blocked_time = OwnerBlockedTime(
                    owner_id=owner_id,
                    blocked_from=blocked_from,
                    blocked_to=blocked_to,
                    reason=reason
                )
                db.add(blocked_time)
                db.commit()
                
                logger.info(f"✅ Заблокировано время для владельца {owner_id}: {blocked_from} - {blocked_to}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка блокировки времени: {e}")
            return False
    
    @staticmethod
    def get_owner_blocked_times(owner_id: int, start_date: datetime, end_date: datetime) -> List[OwnerBlockedTime]:
        """Получить заблокированное время владельца в диапазоне дат"""
        with get_db() as db:
            return db.query(OwnerBlockedTime).filter(
                and_(
                    OwnerBlockedTime.owner_id == owner_id,
                    or_(
                        and_(OwnerBlockedTime.blocked_from >= start_date, OwnerBlockedTime.blocked_from <= end_date),
                        and_(OwnerBlockedTime.blocked_to >= start_date, OwnerBlockedTime.blocked_to <= end_date),
                        and_(OwnerBlockedTime.blocked_from <= start_date, OwnerBlockedTime.blocked_to >= end_date)
                    )
                )
            ).all()
    
    @staticmethod
    def are_both_owners_available(slot_datetime: datetime) -> bool:
        """Проверить, свободны ли оба владельца в указанное время"""
        owners = OwnerService.get_all_owners()
        if len(owners) < 2:
            logger.warning("⚠️ В системе меньше 2 владельцев")
            return False
        
        # Проверяем каждого владельца
        for owner in owners[:2]:  # Берем первых двух владельцев
            if not OwnerService.is_owner_available_at_time(owner.id, slot_datetime):
                return False
        
        return True
    
    @staticmethod
    def is_owner_available_at_time(owner_id: int, slot_datetime: datetime) -> bool:
        """Проверить, доступен ли владелец в конкретное время"""
        day_of_week = slot_datetime.weekday()  # 0=Monday, 6=Sunday
        slot_time_str = slot_datetime.strftime("%H:%M")
        
        # Проверяем, есть ли у владельца такой временной слот
        with get_db() as db:
            time_slot = db.query(OwnerAvailability).filter(
                and_(
                    OwnerAvailability.owner_id == owner_id,
                    OwnerAvailability.day_of_week == day_of_week,
                    OwnerAvailability.time_slot == slot_time_str,
                    OwnerAvailability.is_active == True
                )
            ).first()
            
            if not time_slot:
                return False
            
            # Проверяем заблокированное время
            slot_end = slot_datetime + timedelta(hours=1)  # Встреча длится 1 час
            blocked_times = OwnerService.get_owner_blocked_times(
                owner_id, slot_datetime, slot_end
            )
            
            if blocked_times:
                return False
            
            return True
    
    @staticmethod
    def get_available_slots_for_both_owners(days_ahead: int = 14) -> Dict[str, List[str]]:
        """Получить доступные слоты, когда свободны оба владельца"""
        available_slots = {}
        
        # Генерируем слоты на указанное количество дней вперед
        for day_offset in range(1, days_ahead + 1):
            check_date = datetime.now() + timedelta(days=day_offset)
            
            # Проверяем только рабочие дни (пн-пт)
            if check_date.weekday() >= 5:  # Суббота=5, Воскресенье=6
                continue
            
            date_str = check_date.strftime('%Y-%m-%d')
            day_slots = []
            
            # Проверяем каждый временной слот
            for time_slot in TIME_SLOTS:
                slot_datetime = datetime.combine(
                    check_date.date(),
                    datetime.strptime(time_slot, "%H:%M").time()
                )
                
                if OwnerService.are_both_owners_available(slot_datetime):
                    day_slots.append(time_slot)
            
            if day_slots:
                available_slots[date_str] = day_slots
        
        return available_slots
    
    @staticmethod
    def format_availability_text(owner_id: int) -> str:
        """Форматировать текст доступности владельца по слотам"""
        text = "📅 Ваши временные слоты:\n\n"
        has_slots = False
        
        for day_index, day_name in enumerate(WEEKDAYS):
            slots = OwnerService.get_owner_time_slots(owner_id, day_index)
            if slots:
                has_slots = True
                slots_text = ", ".join(slots)
                text += f"• <b>{day_name}</b>: {slots_text}\n"
        
        if not has_slots:
            return "❌ Временные слоты не настроены\n\n💡 Добавьте слоты для начала приема встреч"
        
        return text