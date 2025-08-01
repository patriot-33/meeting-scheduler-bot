import os
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Complete application settings with all required fields."""
    
    # Telegram Bot (backward compatible)
    telegram_bot_token: str = Field(default="", env="TELEGRAM_BOT_TOKEN", description="Telegram Bot Token")
    telegram_token: Optional[str] = Field(None, env="TELEGRAM_TOKEN", description="Alternative telegram token field")
    admin_telegram_ids: str = Field(default="", env="ADMIN_TELEGRAM_IDS", description="Admin telegram IDs")
    
    # Database
    database_url: str = Field(default="sqlite:///meeting_scheduler.db", env="DATABASE_URL", description="Database connection URL")
    
    # Google Calendar (Enhanced with multiple authentication methods)
    google_calendar_id_1: str = Field(default="primary", env="GOOGLE_CALENDAR_ID_1", description="Primary Google Calendar ID")
    google_calendar_id_2: str = Field(default="", env="GOOGLE_CALENDAR_ID_2", description="Secondary Google Calendar ID")
    
    # Google Service Account - Multiple methods supported
    google_service_account_file: str = Field(
        default="service_account_key.json",
        env="GOOGLE_SERVICE_ACCOUNT_FILE",
        description="Path to Google Service Account JSON file (fallback method)"
    )
    google_service_account_json: Optional[str] = Field(
        None, 
        env="GOOGLE_SERVICE_ACCOUNT_JSON",
        description="Google Service Account JSON as environment variable string (preferred for production)"
    )
    
    # Google OAuth Client - For manager calendar integration
    google_oauth_client_file: str = Field(
        default="oauth_client_key.json",
        env="GOOGLE_OAUTH_CLIENT_FILE", 
        description="Path to Google OAuth Client JSON file"
    )
    google_oauth_client_json: Optional[str] = Field(
        None,
        env="GOOGLE_OAUTH_CLIENT_JSON",
        description="Google OAuth Client JSON as environment variable string (preferred for production)"
    )
    
    # Public OAuth Client ID (for Device Code or Implicit flow)
    google_oauth_client_id: Optional[str] = Field(
        None,
        env="GOOGLE_OAUTH_CLIENT_ID",
        description="Public OAuth Client ID for self-service calendar connection"
    )
    
    # Timezone and Scheduling
    timezone: str = Field(default="Europe/Moscow", env="TIMEZONE", description="Timezone for scheduling")
    
    # Application Settings
    webhook_url: str = Field(default="", env="WEBHOOK_URL", description="Webhook URL for production")
    webhook_path: str = Field(default="/webhook", env="WEBHOOK_PATH", description="Webhook path")
    port: int = Field(default=8443, env="PORT", description="Application port")
    host: str = Field(default="0.0.0.0", env="HOST", description="Application host")
    
    # Feature Flags
    google_calendar_enabled: bool = Field(
        default=True, 
        env="GOOGLE_CALENDAR_ENABLED",
        description="Enable/disable Google Calendar integration"
    )
    fallback_mode: bool = Field(
        default=True, 
        env="FALLBACK_MODE",
        description="Enable fallback functionality when external services are unavailable"
    )
    
    # BULLETPROOF Google Calendar configuration
    google_calendar_try_attendees: bool = Field(
        default=False,  # По умолчанию отключено для избежания ошибок
        env="GOOGLE_CALENDAR_TRY_ATTENDEES",
        description="Try to create events with attendees (requires Domain-Wide Delegation)"
    )
    google_calendar_force_attendee_free: bool = Field(
        default=True,   # По умолчанию включено для bulletproof режима
        env="GOOGLE_CALENDAR_FORCE_ATTENDEE_FREE", 
        description="Force creation of events without attendees (bulletproof mode)"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # Health Check
    health_check_enabled: bool = Field(default=True, description="Enable health check endpoint")
    
    # Development vs Production
    environment: str = Field(default="development", env="ENVIRONMENT", description="Environment: development/production")
    debug: bool = Field(default=False, env="DEBUG", description="Debug mode")
    
    # Database specific
    force_enum_hotfix: bool = Field(default=True, env="FORCE_ENUM_HOTFIX", description="Force enum hotfix for PostgreSQL compatibility")
    
    # Business logic
    meeting_duration_minutes: int = Field(default=60, description="Meeting duration in minutes")
    max_booking_days_ahead: int = Field(default=30, description="Maximum days ahead for booking")
    available_slots: List[str] = Field(
        default=["11:00", "14:00", "15:00", "16:00", "17:00"], 
        description="Available time slots"
    )
    reminder_intervals: List[int] = Field(
        default=[7, 3, 1], 
        description="Reminder intervals in days before meeting"
    )
    
    # Owner management - BULLETPROOF configuration
    expected_owners_count: int = Field(
        default=1, 
        env="EXPECTED_OWNERS_COUNT",
        description="Expected number of owners (1 for single-owner mode, 2+ for multi-owner mode)"
    )
    allow_single_owner_mode: bool = Field(
        default=True,
        env="ALLOW_SINGLE_OWNER_MODE", 
        description="Allow system to work with only 1 owner (bulletproof mode)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def use_webhook(self) -> bool:
        """Determine if webhook should be used."""
        return self.is_production and bool(self.webhook_url)
    
    @property
    def bot_token(self) -> str:
        """Get bot token with backward compatibility."""
        return self.telegram_bot_token or self.telegram_token or ""
    
    @property
    def admin_ids_list(self) -> List[int]:
        """Get admin IDs list with backward compatibility."""
        if self.admin_telegram_ids:
            return [int(id.strip()) for id in self.admin_telegram_ids.split(',') if id.strip()]
        return []
    
    def validate_google_calendar_config(self) -> bool:
        """Validate Google Calendar configuration."""
        if not self.google_calendar_enabled:
            return True
            
        # Check Service Account authentication (for owner calendar)
        has_service_env_json = bool(self.google_service_account_json)
        has_service_file = bool(self.google_service_account_file and os.path.exists(self.google_service_account_file))
        
        # Check OAuth Client authentication (for manager calendars)
        has_oauth_env_json = bool(self.google_oauth_client_json)
        has_oauth_file = bool(self.google_oauth_client_file and os.path.exists(self.google_oauth_client_file))
        
        # Service Account is required for basic functionality
        service_account_valid = has_service_env_json or has_service_file
        
        # OAuth Client is optional but needed for manager integration
        oauth_client_valid = has_oauth_env_json or has_oauth_file
        
        return service_account_valid  # OAuth client validation is separate
    
    def get_google_credentials_info(self) -> dict:
        """Get information about available Google credentials."""
        return {
            "service_account_environment_json_available": bool(self.google_service_account_json),
            "service_account_file_exists": bool(
                self.google_service_account_file and 
                os.path.exists(self.google_service_account_file)
            ),
            "service_account_file_path": self.google_service_account_file,
            "oauth_client_environment_json_available": bool(self.google_oauth_client_json),
            "oauth_client_file_exists": bool(
                self.google_oauth_client_file and 
                os.path.exists(self.google_oauth_client_file)
            ),
            "oauth_client_file_path": self.google_oauth_client_file,
            "google_calendar_enabled": self.google_calendar_enabled,
            "fallback_mode": self.fallback_mode
        }
        
    def validate_oauth_client_config(self) -> bool:
        """Validate OAuth Client configuration for manager integration."""
        has_oauth_env_json = bool(self.google_oauth_client_json)
        has_oauth_file = bool(self.google_oauth_client_file and os.path.exists(self.google_oauth_client_file))
        
        return has_oauth_env_json or has_oauth_file
        
    def get_oauth_client_config(self) -> Optional[dict]:
        """Get OAuth Client configuration from environment or file."""
        import json
        
        # Try environment variable first (preferred for production)
        if self.google_oauth_client_json:
            try:
                return json.loads(self.google_oauth_client_json)
            except json.JSONDecodeError as e:
                logger = __import__('logging').getLogger(__name__)
                logger.error(f"Invalid OAuth Client JSON in environment: {e}")
                return None
        
        # Try file second (development)
        if self.google_oauth_client_file and os.path.exists(self.google_oauth_client_file):
            try:
                with open(self.google_oauth_client_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger = __import__('logging').getLogger(__name__)
                logger.error(f"Invalid OAuth Client JSON in file {self.google_oauth_client_file}: {e}")
                return None
        
        return None
    
    @validator('telegram_bot_token')
    def validate_bot_token(cls, v, values):
        # Allow empty token for testing/development
        if v and len(v) < 10:
            raise ValueError('Telegram bot token must be valid if provided')
        return v
    
    @validator('database_url')
    def validate_database_url(cls, v):
        # Allow empty for testing, will use default SQLite
        if v and not v.startswith(('sqlite:', 'postgresql:')):
            raise ValueError('Database URL must be SQLite or PostgreSQL URL')
        return v or "sqlite:///meeting_scheduler.db"
    
    @validator('admin_telegram_ids')
    def validate_admin_ids(cls, v):
        # Allow empty for testing/development
        if not v:
            return v
        try:
            # Test parsing
            ids = [int(id.strip()) for id in v.split(',') if id.strip()]
            if not ids:
                raise ValueError('At least one valid admin ID is required when provided')
        except ValueError as e:
            raise ValueError(f'Invalid admin Telegram IDs format: {e}')
        return v


# Global settings instance
settings = Settings()


def validate_configuration() -> tuple[bool, list[str]]:
    """Validate application configuration and return status with errors."""
    errors = []
    
    # Required settings
    if not settings.bot_token:
        errors.append("TELEGRAM_BOT_TOKEN is required")
    
    if not settings.database_url:
        errors.append("DATABASE_URL is required")
        
    if not settings.admin_telegram_ids:
        errors.append("ADMIN_TELEGRAM_IDS is required")
    
    # Google Calendar validation (warning, not error if fallback is enabled)
    if settings.google_calendar_enabled:
        if not settings.validate_google_calendar_config():
            if settings.fallback_mode:
                print("⚠️ Warning: Google Calendar not configured, running in fallback mode")
            else:
                errors.append("Google Calendar is enabled but no valid credentials found")
    
    # Production-specific validations
    if settings.is_production:
        if settings.use_webhook and not settings.webhook_url:
            errors.append("WEBHOOK_URL is required in production")
    
    # Owner configuration validation (BULLETPROOF)
    admin_count = len(settings.admin_ids_list)
    expected_count = settings.expected_owners_count
    
    if admin_count == 0:
        errors.append("No admin IDs configured - at least 1 owner is required")
    elif admin_count < expected_count:
        if not settings.allow_single_owner_mode and admin_count == 1:
            errors.append(f"Expected {expected_count} owners but found {admin_count}, and single owner mode is disabled")
        elif admin_count == 1 and expected_count > 1:
            print(f"⚠️ Warning: Expected {expected_count} owners but found {admin_count}. Running in single-owner bulletproof mode.")
        else:
            print(f"⚠️ Warning: Expected {expected_count} owners but found {admin_count}. System will adapt automatically.")
    
    return len(errors) == 0, errors


def print_configuration_summary():
    """Print configuration summary for debugging."""
    print("\n" + "="*50)
    print("CONFIGURATION SUMMARY")
    print("="*50)
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print(f"Port: {settings.port}")
    print(f"Use webhook: {settings.use_webhook}")
    print(f"Log level: {settings.log_level}")
    print(f"Timezone: {settings.timezone}")
    print(f"Admin IDs: {len(settings.admin_ids_list)} configured")
    
    print("\nGoogle Calendar Configuration:")
    creds_info = settings.get_google_credentials_info()
    for key, value in creds_info.items():
        print(f"  {key}: {value}")
    
    print("\nGoogle Calendar BULLETPROOF Settings:")
    print(f"  try_attendees: {settings.google_calendar_try_attendees}")
    print(f"  force_attendee_free: {settings.google_calendar_force_attendee_free}")
    print(f"  strategy: {'Attendee-free (BULLETPROOF)' if settings.google_calendar_force_attendee_free else 'Auto-detect'}")
    
    print("\nBusiness Logic:")
    print(f"  Meeting duration: {settings.meeting_duration_minutes} minutes")
    print(f"  Available slots: {settings.available_slots}")
    print(f"  Reminder intervals: {settings.reminder_intervals} days")
    
    print("\nOwner Management (BULLETPROOF):")
    print(f"  Expected owners count: {settings.expected_owners_count}")
    print(f"  Allow single owner mode: {settings.allow_single_owner_mode}")
    print(f"  Current admin IDs configured: {len(settings.admin_ids_list)}")
    
    print("\nValidation:")
    is_valid, validation_errors = validate_configuration()
    print(f"  Configuration valid: {is_valid}")
    if validation_errors:
        print("  Errors:")
        for error in validation_errors:
            print(f"    - {error}")
    print("="*50 + "\n")