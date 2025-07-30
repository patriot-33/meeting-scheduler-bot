from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
import enum
from datetime import datetime
from contextlib import contextmanager

from src.config import settings

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
    department = Column(Enum(Department), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PENDING)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
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
    status = Column(Enum(MeetingStatus), default=MeetingStatus.SCHEDULED)
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
    """Доступные дни недели и часы для владельцев"""
    __tablename__ = "owner_availability"
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(5), nullable=False)  # "09:00"
    end_time = Column(String(5), nullable=False)    # "18:00"
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

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")