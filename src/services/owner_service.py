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
        """BULLETPROOF: Проверить, свободны ли все необходимые владельцы в указанное время"""
        from config import settings
        
        owners = OwnerService.get_all_owners()
        if len(owners) < 1:
            logger.warning("⚠️ В системе нет владельцев")
            return False
        
        expected_count = settings.expected_owners_count
        actual_count = len(owners)
        
        # Bulletproof mode для одного владельца  
        if actual_count == 1:
            if settings.allow_single_owner_mode:
                logger.info(f"ℹ️ BULLETPROOF режим: 1 владелец из {expected_count} ожидаемых - {owners[0].first_name}")
                return OwnerService.is_owner_available_at_time(owners[0].id, slot_datetime)
            else:
                logger.warning(f"⚠️ Недостаточно владельцев: найден {actual_count}, ожидается {expected_count}, single-mode отключен")
                return False
        
        # Проверяем нужное количество владельцев
        owners_to_check = min(actual_count, expected_count, 2)  # Максимум 2 для совместимости
        logger.info(f"ℹ️ Проверяем доступность {owners_to_check} владельцев из {actual_count} доступных")
        
        for i in range(owners_to_check):
            if not OwnerService.is_owner_available_at_time(owners[i].id, slot_datetime):
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
        """BULLETPROOF LOGIC: Get available slots for all active owners (supports 1+ owners)."""
        available_slots = {}
        
        from services.google_calendar import google_calendar_service
        from database import get_db, User, UserRole
        
        # Get all active owners with their calendar IDs
        with get_db() as db:
            owners = db.query(User).filter(User.role == UserRole.OWNER).all()
            
            if len(owners) == 0:
                logger.warning("⚠️ В системе нет владельцев.")
                return {}
            
            # BULLETPROOF: Используем настройки из конфигурации
            from config import settings
            expected_count = settings.expected_owners_count
            actual_count = len(owners)
            
            # Single owner bulletproof mode
            if actual_count == 1:
                if settings.allow_single_owner_mode:
                    logger.info(f"ℹ️ BULLETPROOF режим: 1 владелец из {expected_count} ожидаемых - {owners[0].first_name}")
                    return OwnerService._get_single_owner_slots(owners[0], days_ahead)
                else:
                    logger.warning(f"⚠️ Single-owner режим отключен, но найден только 1 владелец")
                    return {}
            
            # Multi-owner mode - ищем пересечения слотов
            owners_to_process = min(actual_count, 2)  # Максимум 2 для совместимости
            logger.info(f"ℹ️ BULLETPROOF режим: обрабатываем {owners_to_process} владельцев из {actual_count}")
        
        # Берем первых двух владельцев для совместимости с существующей логикой
        owner1, owner2 = owners[0], owners[1]
        
        # Генерируем слоты на указанное количество дней вперед
        for day_offset in range(1, days_ahead + 1):
            check_date = datetime.now() + timedelta(days=day_offset)
            
            # Проверяем только рабочие дни (пн-пт)
            if check_date.weekday() >= 5:  # Суббота=5, Воскресенье=6
                continue
            
            date_str = check_date.strftime('%Y-%m-%d')
            day_of_week = check_date.weekday()  # 0=понедельник
            
            # STEP 1: Найти общие слоты в локальной базе
            owner1_slots = set(OwnerService.get_owner_time_slots(owner1.id, day_of_week))
            owner2_slots = set(OwnerService.get_owner_time_slots(owner2.id, day_of_week))
            
            # Общие слоты - пересечение множеств
            common_local_slots = owner1_slots.intersection(owner2_slots)
            
            if not common_local_slots:
                continue  # Нет общих слотов в локальной базе
            
            # STEP 2: Проверить каждый общий слот на Google Calendar
            final_slots = []
            
            for time_slot in sorted(common_local_slots):
                slot_datetime = datetime.combine(
                    check_date.date(),
                    datetime.strptime(time_slot, "%H:%M").time()
                )
                
                # Проверить блокировки владельцев
                if (not OwnerService.is_owner_available_at_time(owner1.id, slot_datetime) or 
                    not OwnerService.is_owner_available_at_time(owner2.id, slot_datetime)):
                    continue
                
                # STEP 3: Проверить Google Calendar обоих владельцев
                both_calendars_free = True
                calendar_errors = []
                
                # Проверка календаря первого владельца
                if owner1.google_calendar_id:
                    is_free = OwnerService._check_google_calendar_slot(owner1.google_calendar_id, slot_datetime)
                    if is_free is False:
                        both_calendars_free = False
                    elif is_free is None:
                        calendar_errors.append(f"Овнер 1 ({owner1.first_name})")
                        both_calendars_free = False  # Консервативный подход
                else:
                    logger.warning(f"⚠️ Овнер {owner1.first_name} не подключил Google Calendar")
                    both_calendars_free = False
                
                # Проверка календаря второго владельца
                if both_calendars_free and owner2.google_calendar_id:
                    is_free = OwnerService._check_google_calendar_slot(owner2.google_calendar_id, slot_datetime)
                    if is_free is False:
                        both_calendars_free = False
                    elif is_free is None:
                        calendar_errors.append(f"Овнер 2 ({owner2.first_name})")
                        both_calendars_free = False  # Консервативный подход
                elif both_calendars_free:
                    logger.warning(f"⚠️ Овнер {owner2.first_name} не подключил Google Calendar")
                    both_calendars_free = False
                
                # Логирование ошибок
                if calendar_errors:
                    logger.error(f"❌ Google Calendar недоступен для: {', '.join(calendar_errors)} - слот {time_slot} блокируется")
                
                # Добавляем слот только если оба календаря свободны
                if both_calendars_free:
                    final_slots.append(time_slot)
            
            if final_slots:
                available_slots[date_str] = final_slots
        
        return available_slots
    
    @staticmethod
    def _get_single_owner_slots(owner: User, days_ahead: int) -> Dict[str, List[str]]:
        """Get available slots for a single owner (bulletproof mode for 1 owner)."""
        available_slots = {}
        
        # Генерируем слоты на указанное количество дней вперед
        for day_offset in range(1, days_ahead + 1):
            check_date = datetime.now() + timedelta(days=day_offset)
            
            # Проверяем только рабочие дни (пн-пт)
            if check_date.weekday() >= 5:  # Суббота=5, Воскресенье=6
                continue
            
            date_str = check_date.strftime('%Y-%m-%d')
            day_of_week = check_date.weekday()  # 0=понедельник
            
            # Получаем локальные слоты владельца
            owner_slots = OwnerService.get_owner_time_slots(owner.id, day_of_week)
            
            if not owner_slots:
                continue  # Нет слотов в локальной базе
            
            # Проверяем каждый слот
            final_slots = []
            
            for time_slot in sorted(owner_slots):
                slot_datetime = datetime.combine(
                    check_date.date(),
                    datetime.strptime(time_slot, "%H:%M").time()
                )
                
                # Проверить блокировки владельца
                if not OwnerService.is_owner_available_at_time(owner.id, slot_datetime):
                    continue
                
                # Проверить Google Calendar владельца
                calendar_free = True
                
                if owner.google_calendar_id:
                    is_free = OwnerService._check_google_calendar_slot(owner.google_calendar_id, slot_datetime)
                    if is_free is False:
                        calendar_free = False
                    elif is_free is None:
                        logger.error(f"❌ Google Calendar недоступен для владельца {owner.first_name} - слот {time_slot} блокируется")
                        calendar_free = False  # Консервативный подход
                else:
                    logger.warning(f"⚠️ Владелец {owner.first_name} не подключил Google Calendar")
                    # В режиме одного владельца разрешаем работу без календаря
                    calendar_free = True
                
                # Добавляем слот если календарь свободен
                if calendar_free:
                    final_slots.append(time_slot)
            
            if final_slots:
                available_slots[date_str] = final_slots
        
        return available_slots
    
    @staticmethod
    def _check_google_calendar_slot(calendar_id: str, slot_datetime: datetime) -> Optional[bool]:
        """Check if a specific slot is free in Google Calendar. Returns True/False/None(error)."""
        from services.google_calendar import google_calendar_service
        from services.oauth_service import ManagerOAuthService
        from database import get_db, User
        import json
        
        # First, check if this is an OAuth calendar
        oauth_service = None
        with get_db() as db:
            user = db.query(User).filter(
                User.google_calendar_id == calendar_id,
                User.oauth_credentials.isnot(None)
            ).first()
            
            if user and user.oauth_credentials:
                try:
                    # Use OAuth service for OAuth-connected calendars
                    oauth_credentials = json.loads(user.oauth_credentials)
                    oauth_manager = ManagerOAuthService()
                    oauth_service = oauth_manager.create_calendar_service_from_credentials(oauth_credentials)
                    
                    if oauth_service:
                        logger.info(f"✅ Using OAuth service for calendar check: {calendar_id}")
                except Exception as e:
                    logger.error(f"Failed to create OAuth service: {e}")
                    oauth_service = None
        
        # Use OAuth service if available, otherwise fall back to Service Account
        service_to_use = oauth_service if oauth_service else google_calendar_service._service
        
        if not service_to_use:
            logger.error(f"No service available for calendar {calendar_id}")
            return None  # Calendar service unavailable
        
        try:
            import pytz
            from config import settings
            
            # Определяем часовой пояс
            timezone = pytz.timezone(settings.business_timezone if hasattr(settings, 'business_timezone') else 'Europe/Moscow')
            
            # Если datetime не содержит timezone info, добавляем его
            if slot_datetime.tzinfo is None:
                slot_datetime = timezone.localize(slot_datetime)
            
            slot_end = slot_datetime + timedelta(hours=1)
            
            # Конвертируем в UTC для API
            time_min = slot_datetime.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z')
            time_max = slot_end.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z')
            
            logger.info(f"🔍 Checking calendar {calendar_id} for slot {slot_datetime.strftime('%Y-%m-%d %H:%M %Z')}")
            logger.info(f"🔍 FreeBusy query: {time_min} to {time_max}")
            
            freebusy_query = {
                'timeMin': time_min,
                'timeMax': time_max,
                'items': [{'id': calendar_id}],
                'timeZone': str(timezone)  # Указываем timezone для правильной интерпретации
            }
            
            freebusy_result = service_to_use.freebusy().query(body=freebusy_query).execute()
            
            # Детальное логирование результата
            calendar_data = freebusy_result.get('calendars', {}).get(calendar_id, {})
            busy_times = calendar_data.get('busy', [])
            errors = calendar_data.get('errors', [])
            
            if errors:
                logger.error(f"❌ Calendar API errors for {calendar_id}: {errors}")
                return None
            
            logger.info(f"📊 FreeBusy result for {calendar_id}: {len(busy_times)} busy periods found")
            
            # Логируем каждый занятый период
            for busy_period in busy_times:
                busy_start = busy_period.get('start', 'unknown')
                busy_end = busy_period.get('end', 'unknown')
                logger.info(f"  📌 Busy: {busy_start} to {busy_end}")
            
            is_free = len(busy_times) == 0
            
            if is_free:
                logger.info(f"✅ Slot {slot_datetime.strftime('%Y-%m-%d %H:%M %Z')} is FREE in calendar {calendar_id}")
            else:
                logger.warning(f"❌ Slot {slot_datetime.strftime('%Y-%m-%d %H:%M %Z')} is BUSY in calendar {calendar_id}")
            
            return is_free  # True if no busy times
            
        except Exception as e:
            logger.error(f"Error checking Google Calendar {calendar_id}: {e}")
            return None  # Error occurred
    
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