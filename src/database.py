from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
import enum
from datetime import datetime
from contextlib import contextmanager
import logging

from config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

class UserRole(enum.Enum):
    OWNER = "owner"  # Владелец бизнеса (вы и партнер)
    MANAGER = "manager"  # Руководитель отдела
    PENDING = "pending"  # Ожидает одобрения

class UserStatus(enum.Enum):
    ACTIVE = "active"
    VACATION = "vacation"
    SICK_LEAVE = "sick_leave"
    BUSINESS_TRIP = "business_trip"
    DELETED = "deleted"

class MeetingStatus(enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class Department(enum.Enum):
    FARM = "Фарм отдел"
    FINANCE = "Фин отдел"
    HR = "HR отдел"
    TECH = "Тех отдел"
    IT = "ИТ отдел"
    BIZDEV = "Биздев отдел"
    GAMEDEV = "Геймдев проект"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    telegram_username = Column(String(255))
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255))  # Email для Google Calendar
    google_calendar_id = Column(String(255))  # Персональный ID календаря для владельцев
    department = Column(Enum(Department, name='department', values_callable=lambda x: [e.value for e in x]), nullable=False)
    role = Column(Enum(UserRole, name='userrole', values_callable=lambda x: [e.value for e in x]), default=UserRole.PENDING)
    status = Column(Enum(UserStatus, name='userstatus', values_callable=lambda x: [e.value for e in x]), default=UserStatus.ACTIVE)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    meetings = relationship("Meeting", back_populates="manager")
    reminders = relationship("Reminder", back_populates="user")

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    google_event_id = Column(String(255), unique=True)
    google_meet_link = Column(String(500))
    status = Column(Enum(MeetingStatus, name='meetingstatus', values_callable=lambda x: [e.value for e in x]), default=MeetingStatus.SCHEDULED)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    manager = relationship("User", back_populates="meetings")
    
class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    reminder_type = Column(String(50))  # 'schedule_meeting', 'meeting_1h', etc.
    scheduled_for = Column(DateTime, nullable=False)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="reminders")

class OwnerAvailability(Base):
    """Доступные временные слоты для владельцев по дням недели"""
    __tablename__ = "owner_availability"
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    time_slot = Column(String(5), nullable=False)  # "11:00", "14:00", "15:00" etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    owner = relationship("User", foreign_keys=[owner_id])

class OwnerBlockedTime(Base):
    """Заблокированное время владельцев"""
    __tablename__ = "owner_blocked_time"
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blocked_from = Column(DateTime, nullable=False)
    blocked_to = Column(DateTime, nullable=False)
    reason = Column(String(255))  # Причина блокировки
    created_at = Column(DateTime, server_default=func.now())
    
    owner = relationship("User", foreign_keys=[owner_id])

class Statistics(Base):
    __tablename__ = "statistics"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_meetings = Column(Integer, default=0)
    completed_meetings = Column(Integer, default=0)
    cancelled_meetings = Column(Integer, default=0)
    no_show_meetings = Column(Integer, default=0)
    last_meeting_date = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# Database setup - Optimized for small team (7 people, 1-3 concurrent users)
engine = create_engine(
    settings.database_url,
    pool_size=5,  # Small pool for 7-person team
    max_overflow=2,
    pool_recycle=3600,  # Recycle connections every hour
    pool_pre_ping=True,  # Verify connections before use
    echo=settings.debug,  # Only log SQL in debug mode
    # PostgreSQL-specific settings for better enum handling
    connect_args={
        "options": "-c timezone=UTC"
    } if settings.database_url.startswith('postgresql') else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _ensure_missing_fields_exist():
    """Проверить и добавить отсутствующие поля в таблицу users"""
    try:
        from sqlalchemy import text, inspect
        
        # Проверяем существование колонок
        inspector = inspect(engine)
        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]
        
        # Проверяем email
        if 'email' not in column_names:
            logger.info("Добавляем поле email в таблицу users...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
                conn.commit()
            logger.info("✅ Поле email успешно добавлено")
        else:
            logger.info("✅ Поле email уже существует")
        
        # Проверяем google_calendar_id - CRITICAL FIX
        if 'google_calendar_id' not in column_names:
            logger.info("Добавляем поле google_calendar_id в таблицу users...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN google_calendar_id VARCHAR(255)"))
                conn.commit()
            logger.info("✅ Поле google_calendar_id успешно добавлено")
        else:
            logger.info("✅ Поле google_calendar_id уже существует")
            
    except Exception as e:
        logger.warning(f"⚠️ Не удалось проверить/добавить поля: {e}")
        # Не прерываем инициализацию из-за этого

def init_db():
    """Initialize database with proper enum handling for PostgreSQL."""
    try:
        # For PostgreSQL, we need to handle enum types carefully
        if settings.database_url.startswith('postgresql'):
            logger.info("Initializing PostgreSQL database with enum support...")
            # Create all tables and enum types (не удаляет существующие данные)
            Base.metadata.create_all(bind=engine)
            
            # Проверяем и добавляем отсутствующие поля
            _ensure_missing_fields_exist()
        else:
            # For SQLite and other databases
            Base.metadata.create_all(bind=engine)
            _ensure_missing_fields_exist()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Try to run enum hotfix if it's an enum-related error
        if "enum" in str(e).lower() or "invalid input value" in str(e).lower() or "does not exist" in str(e).lower():
            logger.info("Attempting to fix enum compatibility issues with hotfix...")
            try:
                # Import and run hotfix
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from hotfix_enum import hotfix_enum_database
                hotfix_enum_database()
                logger.info("Database initialization completed after hotfix")
            except Exception as hotfix_error:
                logger.error(f"Hotfix also failed: {hotfix_error}")
                # Fallback to regular creation
                try:
                    Base.metadata.create_all(bind=engine)
                    logger.info("Fallback initialization successful")
                except Exception as fallback_error:
                    logger.error(f"All initialization methods failed: {fallback_error}")
                    raise
        else:
            raise

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")