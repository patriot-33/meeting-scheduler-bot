import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Enhanced application settings with better environment variable support."""
    
    # Telegram Bot
    telegram_token: str = Field(..., description="Telegram Bot Token")
    
    # Database
    database_url: str = Field(..., description="Database connection URL")
    
    # Google Calendar (Enhanced with multiple authentication methods)
    google_calendar_id_1: Optional[str] = Field(None, description="Primary Google Calendar ID")
    google_calendar_id_2: Optional[str] = Field(None, description="Secondary Google Calendar ID")
    
    # Google Service Account - Multiple methods supported
    google_service_account_file: Optional[str] = Field(
        default="service_account_key.json",
        description="Path to Google Service Account JSON file (fallback method)"
    )
    google_service_account_json: Optional[str] = Field(
        None, 
        description="Google Service Account JSON as environment variable string (preferred for production)"
    )
    
    # Application Settings
    webhook_url: Optional[str] = Field(None, description="Webhook URL for production")
    port: int = Field(default=8443, description="Application port")
    host: str = Field(default="0.0.0.0", description="Application host")
    
    # Feature Flags
    google_calendar_enabled: bool = Field(
        default=True, 
        description="Enable/disable Google Calendar integration"
    )
    fallback_mode: bool = Field(
        default=True, 
        description="Enable fallback functionality when external services are unavailable"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # Health Check
    health_check_enabled: bool = Field(default=True, description="Enable health check endpoint")
    
    # Development vs Production
    environment: str = Field(default="development", description="Environment: development/production")
    debug: bool = Field(default=False, description="Debug mode")
    
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
        return self.is_production and self.webhook_url is not None
    
    def validate_google_calendar_config(self) -> bool:
        """Validate Google Calendar configuration."""
        if not self.google_calendar_enabled:
            return True
            
        # Check if any authentication method is available
        has_env_json = bool(self.google_service_account_json)
        has_file = bool(self.google_service_account_file and os.path.exists(self.google_service_account_file))
        
        # In production, prefer environment variable
        if self.is_production:
            return has_env_json or has_file
        
        # In development, file is acceptable
        return has_env_json or has_file
    
    def get_google_credentials_info(self) -> dict:
        """Get information about available Google credentials."""
        return {
            "environment_json_available": bool(self.google_service_account_json),
            "service_account_file_exists": bool(
                self.google_service_account_file and 
                os.path.exists(self.google_service_account_file)
            ),
            "service_account_file_path": self.google_service_account_file,
            "google_calendar_enabled": self.google_calendar_enabled,
            "fallback_mode": self.fallback_mode
        }


# Global settings instance
settings = Settings()


def validate_configuration() -> tuple[bool, list[str]]:
    """Validate application configuration and return status with errors."""
    errors = []
    
    # Required settings
    if not settings.telegram_token:
        errors.append("TELEGRAM_TOKEN is required")
    
    if not settings.database_url:
        errors.append("DATABASE_URL is required")
    
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
    
    print("\nGoogle Calendar Configuration:")
    creds_info = settings.get_google_credentials_info()
    for key, value in creds_info.items():
        print(f"  {key}: {value}")
    
    print("\nValidation:")
    is_valid, validation_errors = validate_configuration()
    print(f"  Configuration valid: {is_valid}")
    if validation_errors:
        print("  Errors:")
        for error in validation_errors:
            print(f"    - {error}")
    print("="*50 + "\n")