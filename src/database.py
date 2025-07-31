from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Text, text
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
    google_calendar_id = Column(String(255))  # Персональный ID календаря
    oauth_credentials = Column(Text)  # OAuth токены для руководителей
    calendar_connected = Column(Boolean, default=False)  # Статус подключения календаря
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
    google_calendar_id = Column(String(255))  # Calendar where event was created
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

# BULLETPROOF Database setup - Database-agnostic with optimized settings
if settings.database_url.startswith('postgresql'):
    # PostgreSQL with connection pooling
    engine = create_engine(
        settings.database_url,
        pool_size=5,  # Small pool for 7-person team
        max_overflow=3,  # Increased overflow for peak usage
        pool_recycle=3600,  # Recycle connections every hour
        pool_pre_ping=True,  # Verify connections before use
        pool_timeout=30,  # Timeout for getting connection from pool
        echo=settings.debug,  # Only log SQL in debug mode
        connect_args={
            "options": "-c timezone=UTC",
            "application_name": "meeting_scheduler_bot"
        }
    )
elif settings.database_url.startswith('sqlite'):
    # SQLite with optimized settings (no connection pooling)
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,  # Only log SQL in debug mode
        pool_pre_ping=True,  # Still verify connections
        connect_args={
            "check_same_thread": False,  # Allow multi-threading
            "timeout": 20  # SQLite lock timeout
        }
    )
else:
    # Generic database fallback
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=settings.debug
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
        
        # Проверяем oauth_credentials - NEW OAUTH FIELD
        if 'oauth_credentials' not in column_names:
            logger.info("Добавляем поле oauth_credentials в таблицу users...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN oauth_credentials TEXT"))
                conn.commit()
            logger.info("✅ Поле oauth_credentials успешно добавлено")
        else:
            logger.info("✅ Поле oauth_credentials уже существует")
        
        # Проверяем calendar_connected - NEW BOOLEAN FIELD
        if 'calendar_connected' not in column_names:
            logger.info("Добавляем поле calendar_connected в таблицу users...")
            with engine.connect() as conn:
                if settings.database_url.startswith('postgresql'):
                    conn.execute(text("ALTER TABLE users ADD COLUMN calendar_connected BOOLEAN DEFAULT FALSE"))
                else:
                    # SQLite uses 0/1 for boolean
                    conn.execute(text("ALTER TABLE users ADD COLUMN calendar_connected BOOLEAN DEFAULT 0"))
                conn.commit()
            logger.info("✅ Поле calendar_connected успешно добавлено")
        else:
            logger.info("✅ Поле calendar_connected уже существует")
        
        # Check meetings table for google_calendar_id column
        meetings_columns = [col['name'] for col in inspector.get_columns('meetings')]
        if 'google_calendar_id' not in meetings_columns:
            logger.info("Добавляем поле google_calendar_id в таблицу meetings...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE meetings ADD COLUMN google_calendar_id VARCHAR(255)"))
                conn.commit()
            logger.info("✅ Поле google_calendar_id в meetings успешно добавлено")
        else:
            logger.info("✅ Поле google_calendar_id в meetings уже существует")
            
    except Exception as e:
        logger.warning(f"⚠️ Не удалось проверить/добавить поля: {e}")
        # Не прерываем инициализацию из-за этого

def init_db():
    """Initialize database with bulletproof error handling and auto-migration."""
    logger.info("🚀 DATABASE INIT: ========== STARTING ==========")
    logger.info("🚀 Initializing database with bulletproof system...")
    
    try:
        # Test database connection first
        logger.info("🚀 DATABASE: Testing connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            logger.info(f"🚀 DATABASE: ✅ Connection successful: {result}")
        
        # For PostgreSQL, we need to handle enum types carefully
        if settings.database_url.startswith('postgresql'):
            logger.info("🚀 DATABASE: Initializing PostgreSQL with enum support...")
            # Create all tables and enum types (не удаляет существующие данные)
            logger.info("🚀 DATABASE: Creating all tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("🚀 DATABASE: ✅ Tables created successfully")
            
            # Проверяем и добавляем отсутствующие поля
            _ensure_missing_fields_exist()
        else:
            # For SQLite and other databases
            Base.metadata.create_all(bind=engine)
            _ensure_missing_fields_exist()
        
        # Run automatic migration if needed
        try:
            from migrations.add_calendar_connected_field import upgrade
            upgrade()
            logger.info("✅ Auto-migration completed successfully")
        except Exception as migration_error:
            logger.warning(f"Auto-migration skipped (may be normal): {migration_error}")
        
        logger.info("✅ Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Try to run enum hotfix if it's an enum-related error
        if "enum" in str(e).lower() or "invalid input value" in str(e).lower() or "does not exist" in str(e).lower():
            logger.info("Attempting to fix enum compatibility issues with bulletproof fallback...")
            try:
                # BULLETPROOF: Database-specific enum handling
                if settings.database_url.startswith('postgresql'):
                    logger.info("Applying PostgreSQL enum fixes...")
                    with engine.connect() as conn:
                        # Drop conflicting enum types
                        conn.execute(text("DROP TYPE IF EXISTS department CASCADE"))
                        conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))  
                        conn.execute(text("DROP TYPE IF EXISTS userstatus CASCADE"))
                        conn.commit()
                    logger.info("Dropped existing enum types")
                
                # Recreate all tables with fresh schema
                Base.metadata.drop_all(bind=engine, checkfirst=True)
                Base.metadata.create_all(bind=engine)
                logger.info("✅ Database initialization successful with enum fixes")
                
            except Exception as enum_fix_error:
                logger.error(f"Enum fix failed: {enum_fix_error}")
                
                # Final bulletproof fallback
                try:
                    Base.metadata.create_all(bind=engine, checkfirst=True)
                    logger.info("✅ Bulletproof fallback initialization successful")
                except Exception as final_error:
                    logger.error(f"❌ All initialization methods failed: {final_error}")
                    raise
        else:
            raise

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")