import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    admin_telegram_ids: str = Field(..., env="ADMIN_TELEGRAM_IDS")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Google Calendar
    google_calendar_id_1: str = Field(..., env="GOOGLE_CALENDAR_ID_1")
    google_calendar_id_2: str = Field(..., env="GOOGLE_CALENDAR_ID_2")
    google_service_account_file: str = Field(
        default="service_account_key.json",
        env="GOOGLE_SERVICE_ACCOUNT_FILE"
    )
    
    # Timezone
    timezone: str = Field(default="Europe/Moscow", env="TIMEZONE")
    
    # Application
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    force_enum_hotfix: bool = Field(default=True, env="FORCE_ENUM_HOTFIX")
    
    # Webhook (optional)
    webhook_url: str = Field(default="", env="WEBHOOK_URL")
    webhook_path: str = Field(default="/webhook", env="WEBHOOK_PATH")
    port: int = Field(default=8443, env="PORT")
    
    # Business logic
    meeting_duration_minutes: int = 60
    max_booking_days_ahead: int = 30
    available_slots: List[str] = ["11:00", "14:00", "15:00", "16:00", "17:00"]
    reminder_intervals: List[int] = [7, 3, 1]  # days before meeting
    
    class Config:
        env_file = ".env"
        
    @property
    def admin_ids_list(self) -> List[int]:
        if isinstance(self.admin_telegram_ids, str):
            return [int(id.strip()) for id in self.admin_telegram_ids.split(',') if id.strip()]
        return self.admin_telegram_ids
    
    @validator('telegram_bot_token')
    def validate_bot_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Telegram bot token is required and must be valid')
        return v
    
    @validator('database_url')
    def validate_database_url(cls, v):
        if not v:
            raise ValueError('Database URL is required')
        # Поддерживаем PostgreSQL и SQLite для локального тестирования
        if not (v.startswith('postgresql') or v.startswith('sqlite')):
            raise ValueError('PostgreSQL or SQLite database URL is required')
        return v

settings = Settings()
