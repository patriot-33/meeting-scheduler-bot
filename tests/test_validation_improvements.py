"""
🛡️ VALIDATION IMPROVEMENTS TESTS
Comprehensive tests for validation patterns based on root cause analysis.
Focus on preventing the validation gaps that caused 3/4 previous bugs.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class TestEnvironmentValidation:
    """Test comprehensive environment validation"""
    
    def test_required_env_vars_validation(self):
        """Test that all required environment variables are validated"""
        from config import validate_configuration
        
        # Test with missing required vars (mock empty environment)
        with patch.dict(os.environ, {}, clear=True):
            is_valid, errors = validate_configuration()
            
            # Should detect missing required variables
            assert not is_valid
            assert len(errors) > 0
            
            # Should specifically mention required variables
            error_text = ' '.join(errors)
            assert "TELEGRAM_BOT_TOKEN" in error_text or "bot token" in error_text.lower()
    
    def test_google_calendar_config_validation(self):
        """Test Google Calendar configuration validation"""
        from config import settings
        
        # Test validation method exists
        assert hasattr(settings, 'validate_google_calendar_config')
        
        # Test that it returns boolean
        result = settings.validate_google_calendar_config()
        assert isinstance(result, bool)
    
    def test_credentials_info_method(self):
        """Test that credentials info method provides diagnostic information"""
        from config import settings
        
        creds_info = settings.get_google_credentials_info()
        
        # Should provide detailed information about credential availability
        assert isinstance(creds_info, dict)
        assert "service_account_environment_json_available" in creds_info
        assert "service_account_file_exists" in creds_info
        assert "oauth_client_environment_json_available" in creds_info
    
    @patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test_token_123',
        'ADMIN_TELEGRAM_IDS': '123,456',
        'DATABASE_URL': 'sqlite:///test.db'
    })
    def test_valid_environment_passes_validation(self):
        """Test that valid environment passes validation"""
        from config import validate_configuration
        
        is_valid, errors = validate_configuration()
        
        # With minimal required vars, should be valid (or have only warnings)
        assert is_valid or len([e for e in errors if "required" in e.lower()]) == 0


class TestInputValidation:
    """Test input validation across handlers"""
    
    def test_telegram_id_validation(self):
        """Test that Telegram IDs are properly validated"""
        from config import settings
        
        # Test admin IDs parsing
        with patch.dict(os.environ, {'ADMIN_TELEGRAM_IDS': '123,abc,456'}):
            from config import Settings
            test_settings = Settings()
            
            # Should handle invalid IDs gracefully
            try:
                admin_ids = test_settings.admin_ids_list
                # Should only include valid numeric IDs
                assert all(isinstance(id_val, int) for id_val in admin_ids)
            except ValueError:
                # Or raise appropriate validation error
                pass
    
    def test_database_url_validation(self):
        """Test database URL validation"""
        from config import settings
        
        # Test with invalid database URL
        with patch.dict(os.environ, {'DATABASE_URL': 'invalid://url'}):
            from config import Settings
            
            try:
                test_settings = Settings()
                # Should either use default or raise validation error
                assert test_settings.database_url.startswith(('sqlite:', 'postgresql:'))
            except ValueError:
                # Validation error is acceptable
                pass


class TestApiErrorHandling:
    """Test API error handling improvements"""
    
    def test_telegram_api_error_handling(self):
        """Test that Telegram API errors are handled"""
        main_path = Path(__file__).parent.parent / "src" / "main.py"
        
        with open(main_path, 'r') as f:
            content = f.read()
        
        # Should have specific handling for Telegram errors
        assert "TelegramError" in content or "telegram.error" in content
        assert "BadRequest" in content
    
    def test_google_api_error_handling(self):
        """Test Google API error handling"""
        google_service_path = Path(__file__).parent.parent / "src" / "services" / "google_calendar.py"
        
        if not google_service_path.exists():
            pytest.skip("Google calendar service not found")
            
        with open(google_service_path, 'r') as f:
            content = f.read()
        
        # Should have error handling for Google API
        assert "try:" in content and "except" in content
        # Should handle Google API specific errors
        google_error_patterns = ["googleapiclient", "HttpError", "HttpAccessTokenRefreshError"]
        assert any(pattern in content for pattern in google_error_patterns)


class TestBusinessLogicValidation:
    """Test business logic validation"""
    
    def test_meeting_duration_validation(self):
        """Test meeting duration is validated"""
        from config import settings
        
        assert settings.meeting_duration_minutes > 0
        assert settings.meeting_duration_minutes <= 480  # Max 8 hours
    
    def test_available_slots_validation(self):
        """Test available slots are validated"""
        from config import settings
        
        # Should have some available slots
        assert len(settings.available_slots) > 0
        
        # Each slot should be valid time format
        for slot in settings.available_slots:
            assert isinstance(slot, str)
            assert ":" in slot  # Basic time format check
    
    def test_admin_count_validation(self):
        """Test admin count validation based on BULLETPROOF configuration"""
        from config import settings
        
        # Should have admin count properties
        assert hasattr(settings, 'expected_owners_count')
        assert hasattr(settings, 'allow_single_owner_mode')
        
        # Expected count should be positive
        assert settings.expected_owners_count > 0


class TestRealTimeValidation:
    """Test real-time validation capabilities"""
    
    def test_health_check_endpoint(self):
        """Test health check provides real-time validation"""
        try:
            from utils.health_check import health_check
            
            health_result = health_check()
            
            # Should provide comprehensive health information
            assert isinstance(health_result, dict)
            assert 'status' in health_result
            
            # Should check multiple components
            expected_checks = ['database', 'configuration']
            result_str = str(health_result).lower()
            
            # At least some component checks should be present
            assert any(check in result_str for check in expected_checks)
            
        except ImportError:
            pytest.skip("Health check not available")
    
    def test_database_health_validation(self):
        """Test database health validation"""
        try:
            from utils.database_health import check_database_health
            
            # Should be able to check database health
            db_health = check_database_health()
            assert isinstance(db_health, dict)
            
        except ImportError:
            pytest.skip("Database health check not available")


class TestPreventiveValidation:
    """Test preventive validation measures"""
    
    def test_startup_validation_sequence(self):
        """Test that startup includes comprehensive validation"""
        main_path = Path(__file__).parent.parent / "src" / "main.py"
        
        with open(main_path, 'r') as f:
            content = f.read()
        
        # Should have health check before startup
        assert "health_check" in content
        assert "validate" in content
        
        # Should have database initialization
        assert "init_db" in content
    
    def test_configuration_summary_logging(self):
        """Test that configuration is logged for diagnostics"""
        from config import print_configuration_summary
        
        # Should be able to print config summary without errors
        try:
            print_configuration_summary()
        except Exception as e:
            pytest.fail(f"Configuration summary failed: {e}")
    
    def test_migration_safety_checks(self):
        """Test that migrations have safety checks"""
        migration_files = list(Path(__file__).parent.parent.glob("migrations/*.py"))
        
        if not migration_files:
            pytest.skip("No migration files found")
        
        for migration_file in migration_files:
            with open(migration_file, 'r') as f:
                content = f.read()
            
            # Should have some error handling
            assert "try:" in content or "except" in content, f"Migration {migration_file.name} lacks error handling"


class TestErrorRecoveryValidation:
    """Test error recovery and fallback validation"""
    
    def test_fallback_mode_configuration(self):
        """Test fallback mode is properly configured"""
        from config import settings
        
        # Should have fallback mode setting
        assert hasattr(settings, 'fallback_mode')
        assert isinstance(settings.fallback_mode, bool)
    
    def test_graceful_degradation_patterns(self):
        """Test graceful degradation patterns"""
        # Check if Google Calendar service has fallback handling
        google_service_path = Path(__file__).parent.parent / "src" / "services" / "google_calendar.py"
        
        if not google_service_path.exists():
            pytest.skip("Google calendar service not found")
            
        with open(google_service_path, 'r') as f:
            content = f.read()
        
        # Should have fallback or graceful degradation
        fallback_patterns = ["fallback", "graceful", "degrade", "alternative"]
        assert any(pattern in content.lower() for pattern in fallback_patterns)


class TestValidationDocumentation:
    """Test that validation patterns are documented"""
    
    def test_bug_report_lessons_implemented(self):
        """Test that lessons from bug report are implemented as validation"""
        bug_report_path = Path(__file__).parent.parent / "bug_report_2025_08_01.json"
        
        if not bug_report_path.exists():
            pytest.skip("Bug report not found")
        
        import json
        with open(bug_report_path, 'r') as f:
            bug_data = json.load(f)
        
        # Get prevention measures from lessons learned
        prevention_measures = bug_data.get("lessons_learned", {}).get("prevention_measures", [])
        
        # Should have specific prevention measures documented
        assert len(prevention_measures) > 0
        
        # Key prevention patterns should be mentioned
        prevention_text = ' '.join(prevention_measures).lower()
        validation_keywords = ["startup check", "health check", "validation", "test"]
        
        assert any(keyword in prevention_text for keyword in validation_keywords)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])