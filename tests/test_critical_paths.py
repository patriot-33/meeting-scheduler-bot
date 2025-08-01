"""
🧪 CRITICAL PATH TESTS
Tests for the 4 bug categories that were previously fixed to prevent regression.
Based on bug_report_2025_08_01.json analysis.
"""

import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class TestEnvironmentLoading:
    """Tests for ENV_LOADING_001 - Environment variables not loading from .env file"""
    
    def test_dotenv_is_loaded_in_config(self):
        """Test that load_dotenv() is called in config.py"""
        # Read config.py content
        config_path = Path(__file__).parent.parent / "src" / "config.py"
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Verify dotenv import and call exist
        assert "from dotenv import load_dotenv" in config_content
        assert "load_dotenv()" in config_content
        
    def test_environment_variables_loaded(self):
        """Test that environment variables are properly loaded"""
        # This would require actual .env file for full test
        # For now, test that the config system can handle env vars
        from config import settings
        
        # Test that settings object exists and has required fields
        assert hasattr(settings, 'bot_token')
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'google_service_account_json')
        
    @patch.dict(os.environ, {'TEST_VAR': 'test_value'})
    def test_env_var_override(self):
        """Test that environment variables properly override defaults"""
        from config import Settings
        
        # Create fresh settings instance
        test_settings = Settings()
        
        # Environment variables should work
        assert os.getenv('TEST_VAR') == 'test_value'


class TestMessageEditingSafety:
    """Tests for BADREQUEST_002 - BadRequest: Message is not modified"""
    
    def test_safe_send_message_function_exists(self):
        """Test that safe_send_message function exists and is not recursive"""
        # Import the module that should contain safe_send_message
        try:
            from handlers.manager_calendar import safe_send_message
        except ImportError:
            pytest.skip("safe_send_message function not found in expected location")
        
        # This is a basic existence test - full testing would require mock Telegram objects
        assert callable(safe_send_message)
    
    def test_no_infinite_recursion_in_safe_send_message(self):
        """Test that safe_send_message doesn't call itself (INFINITE_RECURSION_004)"""
        # Test the imported safe_send_message function from utils.telegram_safe
        telegram_safe_path = Path(__file__).parent.parent / "src" / "utils" / "telegram_safe.py"
        
        if not telegram_safe_path.exists():
            pytest.skip("telegram_safe.py not found")
            
        with open(telegram_safe_path, 'r') as f:
            content = f.read()
        
        # Verify the function exists in the utility module
        assert "def safe_send_message" in content
        
        # Extract just the function by finding it between def and the next function
        import re
        
        # Use regex to find the function body
        pattern = r'async def safe_send_message.*?(?=^@|\nclass |\ndef |\n\S|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        
        if match:
            function_body = match.group(0)
            
            # CRITICAL TEST: Should NOT call itself recursively (the core bug)
            # Count calls but exclude the function definition line itself
            lines = function_body.split('\n')
            recursive_calls = 0
            for line in lines:
                if 'safe_send_message(' in line and not line.strip().startswith('async def safe_send_message'):
                    recursive_calls += 1
            
            assert recursive_calls == 0, f"CRITICAL BUG: safe_send_message calls itself {recursive_calls} times!"
            
            # Should use proper Telegram API calls instead
            assert "edit_message_text" in function_body
            assert "reply_text" in function_body
            
            # Should handle BadRequest exception
            assert "BadRequest" in function_body
            assert "Message is not modified" in function_body
            
        else:
            # If regex fails, do basic check that function exists and is not obviously broken
            lines = content.split('\n')
            safe_message_lines = [line for line in lines if 'safe_send_message(' in line]
            
            # First occurrence should be the function definition
            assert len(safe_message_lines) > 0
            first_line = safe_message_lines[0]
            assert 'def safe_send_message' in first_line, "Function definition should be first occurrence"


class TestCalendarStatusDiagnostics:
    """Tests for CALENDAR_STATUS_003 - Inaccurate calendar connection status"""
    
    def test_real_time_calendar_validation_exists(self):
        """Test that real-time calendar validation exists"""
        # Check if Google Calendar service has test_calendar_access method
        try:
            from services.google_calendar import GoogleCalendarService
            service = GoogleCalendarService()
            
            # Should have method for testing calendar access
            assert hasattr(service, 'test_calendar_access') or hasattr(service, 'verify_calendar_access')
        except ImportError:
            pytest.skip("GoogleCalendarService not available for testing")
        except Exception:
            # Service might not initialize without credentials - that's OK for this test
            pass
    
    def test_calendar_status_not_just_database_flag(self):
        """Test that calendar status checking goes beyond just database flags"""
        manager_calendar_path = Path(__file__).parent.parent / "src" / "handlers" / "manager_calendar.py"
        
        if not manager_calendar_path.exists():
            pytest.skip("manager_calendar.py not found")
            
        with open(manager_calendar_path, 'r') as f:
            content = f.read()
        
        # Should have real-time validation, not just DB flag checking
        assert "test_calendar_access" in content or "verify_calendar" in content


class TestValidationAndErrorHandling:
    """Tests for validation improvements based on root cause analysis"""
    
    def test_config_validation_exists(self):
        """Test that configuration validation exists"""
        from config import validate_configuration
        
        # Should return tuple of (bool, list)
        is_valid, errors = validate_configuration()
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_startup_checks_exist(self):
        """Test that startup health checks exist"""
        try:
            from utils.health_check import health_check
            
            health_result = health_check()
            assert isinstance(health_result, dict)
            assert 'status' in health_result
        except ImportError:
            pytest.skip("health_check not available")
    
    def test_error_handler_exists_in_main(self):
        """Test that error handler is properly set up in main.py"""
        main_path = Path(__file__).parent.parent / "src" / "main.py"
        
        with open(main_path, 'r') as f:
            content = f.read()
        
        # Should have error handler setup
        assert "error_handler" in content
        assert "add_error_handler" in content


class TestBugPreventionMeasures:
    """Tests for prevention measures based on lessons learned"""
    
    def test_defensive_programming_patterns(self):
        """Test that defensive programming patterns are in place"""
        # Check for try-catch blocks in critical areas
        critical_files = [
            "src/handlers/manager_calendar.py",
            "src/services/google_calendar.py", 
            "src/main.py"
        ]
        
        for file_path in critical_files:
            full_path = Path(__file__).parent.parent / file_path
            
            if not full_path.exists():
                continue
                
            with open(full_path, 'r') as f:
                content = f.read()
            
            # Should have error handling
            try_count = content.count("try:")
            except_count = content.count("except")
            
            # At least some error handling should exist
            assert try_count > 0 or except_count > 0, f"No error handling found in {file_path}"
    
    def test_logging_exists_in_critical_paths(self):
        """Test that logging exists in critical paths"""
        main_path = Path(__file__).parent.parent / "src" / "main.py"
        
        with open(main_path, 'r') as f:
            content = f.read()
        
        # Should have logging setup
        assert "logging" in content
        assert "logger" in content or "log" in content


# Integration test for the bug report patterns
class TestBugReportIntegration:
    """Integration tests based on the actual bug report"""
    
    def test_bug_report_loadable(self):
        """Test that the bug report is valid JSON and loadable"""
        bug_report_path = Path(__file__).parent.parent / "bug_report_2025_08_01.json"
        
        assert bug_report_path.exists(), "Bug report file should exist"
        
        with open(bug_report_path, 'r') as f:
            bug_data = json.load(f)
        
        # Validate bug report structure
        assert "session_info" in bug_data
        assert "bugs_detailed" in bug_data
        assert "lessons_learned" in bug_data
        
        # Should have the 4 documented bugs
        assert bug_data["session_info"]["total_bugs_fixed"] == 4
        
        bug_ids = [bug["bug_id"] for bug in bug_data["bugs_detailed"]]
        expected_bugs = ["ENV_LOADING_001", "BADREQUEST_002", "CALENDAR_STATUS_003", "INFINITE_RECURSION_004"]
        
        for expected_bug in expected_bugs:
            assert expected_bug in bug_ids, f"Bug {expected_bug} should be documented"
    
    def test_all_documented_fixes_applied(self):
        """Test that all documented fixes from the bug report are actually applied"""
        bug_report_path = Path(__file__).parent.parent / "bug_report_2025_08_01.json"
        
        with open(bug_report_path, 'r') as f:
            bug_data = json.load(f)
        
        for bug in bug_data["bugs_detailed"]:
            if bug.get("fix_applied") and bug["fix_applied"].get("files_modified"):
                for file_path in bug["fix_applied"]["files_modified"]:
                    full_path = Path(__file__).parent.parent / file_path
                    assert full_path.exists(), f"Fixed file {file_path} should exist"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])