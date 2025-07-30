"""
Сервис управления владельцами бизнеса
"""
import logging
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.database import get_db, User, UserRole, OwnerAvailability, OwnerBlockedTime
from src.config import settings

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
    def set_owner_availability(owner_id: int, day_of_week: int, start_time: str, end_time: str) -> bool:
        """Установить доступность владельца на конкретный день"""
        try:
            with get_db() as db:
                # Удаляем старую доступность для этого дня
                db.query(OwnerAvailability).filter(
                    and_(
                        OwnerAvailability.owner_id == owner_id,
                        OwnerAvailability.day_of_week == day_of_week
                    )
                ).delete()
                
                # Добавляем новую доступность
                availability = OwnerAvailability(
                    owner_id=owner_id,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    is_active=True
                )
                db.add(availability)
                db.commit()
                
                logger.info(f"✅ Установлена доступность для владельца {owner_id}: {WEEKDAYS[day_of_week]} {start_time}-{end_time}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка установки доступности: {e}")
            return False
    
    @staticmethod
    def remove_owner_availability(owner_id: int, day_of_week: int) -> bool:
        """Удалить доступность владельца на конкретный день"""
        try:
            with get_db() as db:
                db.query(OwnerAvailability).filter(
                    and_(
                        OwnerAvailability.owner_id == owner_id,
                        OwnerAvailability.day_of_week == day_of_week
                    )
                ).delete()
                db.commit()
                
                logger.info(f"✅ Удалена доступность для владельца {owner_id}: {WEEKDAYS[day_of_week]}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка удаления доступности: {e}")
            return False
    
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
        slot_time = slot_datetime.time()
        
        # Проверяем общую доступность по дням недели
        with get_db() as db:
            availability = db.query(OwnerAvailability).filter(
                and_(
                    OwnerAvailability.owner_id == owner_id,
                    OwnerAvailability.day_of_week == day_of_week,
                    OwnerAvailability.is_active == True
                )
            ).first()
            
            if not availability:
                return False
            
            # Проверяем, входит ли время в рабочие часы
            start_time = datetime.strptime(availability.start_time, "%H:%M").time()
            end_time = datetime.strptime(availability.end_time, "%H:%M").time()
            
            if not (start_time <= slot_time <= end_time):
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
    def get_available_slots_for_both_owners(days_ahead: int = 14) -> List[datetime]:
        """Получить доступные слоты, когда свободны оба владельца"""
        available_slots = []
        
        # Генерируем слоты на указанное количество дней вперед
        for day_offset in range(1, days_ahead + 1):
            check_date = datetime.now() + timedelta(days=day_offset)
            
            # Проверяем только рабочие дни (пн-пт)
            if check_date.weekday() >= 5:  # Суббота=5, Воскресенье=6
                continue
            
            # Проверяем каждый временной слот
            for time_slot in TIME_SLOTS:
                slot_datetime = datetime.combine(
                    check_date.date(),
                    datetime.strptime(time_slot, "%H:%M").time()
                )
                
                if OwnerService.are_both_owners_available(slot_datetime):
                    available_slots.append(slot_datetime)
        
        return available_slots
    
    @staticmethod
    def format_availability_text(owner_id: int) -> str:
        """Форматировать текст доступности владельца"""
        availability = OwnerService.get_owner_availability(owner_id)
        
        if not availability:
            return "❌ Доступность не настроена"
        
        text = "📅 Ваша текущая доступность:\n\n"
        
        for avail in availability:
            day_name = WEEKDAYS[avail.day_of_week]
            text += f"• {day_name}: {avail.start_time} - {avail.end_time}\n"
        
        return text