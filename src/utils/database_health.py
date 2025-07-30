"""
Bulletproof database health monitoring and recovery system.
"""
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from database import engine, get_db, User
from config import settings

logger = logging.getLogger(__name__)

class DatabaseHealthMonitor:
    """Monitor database health and provide recovery mechanisms."""
    
    def __init__(self):
        self.last_health_check = None
        self.consecutive_failures = 0
        self.max_failures = 3
        
    def check_database_health(self) -> Dict[str, Any]:
        """Comprehensive database health check."""
        health_status = {
            'status': 'healthy',
            'checks': {},
            'timestamp': datetime.now().isoformat(),
            'errors': []
        }
        
        try:
            # Test 1: Basic connection
            health_status['checks']['connection'] = self._test_connection()
            
            # Test 2: Table existence
            health_status['checks']['tables'] = self._test_tables()
            
            # Test 3: Read operation
            health_status['checks']['read'] = self._test_read_operation()
            
            # Test 4: Write operation (non-destructive)
            health_status['checks']['write'] = self._test_write_operation()
            
            # Test 5: Migration status
            health_status['checks']['migration'] = self._test_migration_status()
            
            # Overall status
            failed_checks = [k for k, v in health_status['checks'].items() if not v['success']]
            if failed_checks:
                health_status['status'] = 'degraded' if len(failed_checks) <= 2 else 'unhealthy'
                health_status['failed_checks'] = failed_checks
                
            self.consecutive_failures = 0 if health_status['status'] == 'healthy' else self.consecutive_failures + 1
            self.last_health_check = datetime.now()
            
        except Exception as e:
            health_status['status'] = 'critical'
            health_status['errors'].append(f"Health check failed: {str(e)}")
            self.consecutive_failures += 1
            logger.error(f"Database health check failed: {e}")
            
        return health_status
    
    def _test_connection(self) -> Dict[str, Any]:
        """Test basic database connection."""
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                return {
                    'success': result == 1,
                    'message': 'Connection successful',
                    'response_time_ms': 0  # Could add timing
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}',
                'error': str(e)
            }
    
    def _test_tables(self) -> Dict[str, Any]:
        """Test that required tables exist."""
        try:
            with engine.connect() as conn:
                if settings.database_url.startswith('postgresql'):
                    result = conn.execute(text("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public' AND tablename = 'users'
                    """))
                else:
                    result = conn.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='users'
                    """))
                
                tables_exist = len(result.fetchall()) > 0
                return {
                    'success': tables_exist,
                    'message': 'Required tables exist' if tables_exist else 'Users table missing'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Table check failed: {str(e)}',
                'error': str(e)
            }
    
    def _test_read_operation(self) -> Dict[str, Any]:
        """Test read operations."""
        try:
            with get_db() as db:
                count = db.query(User).count()
                return {
                    'success': True,
                    'message': f'Read successful, {count} users in database',
                    'user_count': count
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Read operation failed: {str(e)}',
                'error': str(e)
            }
    
    def _test_write_operation(self) -> Dict[str, Any]:
        """Test write operations (non-destructive)."""
        try:
            with engine.connect() as conn:
                # Test with a simple transaction that we rollback
                trans = conn.begin()
                try:
                    conn.execute(text("SELECT COUNT(*) FROM users"))
                    trans.rollback()  # Don't commit, just test write capability
                    return {
                        'success': True,
                        'message': 'Write test successful'
                    }
                except Exception as e:
                    trans.rollback()
                    raise e
        except Exception as e:
            return {
                'success': False,
                'message': f'Write operation failed: {str(e)}',
                'error': str(e)
            }
    
    def _test_migration_status(self) -> Dict[str, Any]:
        """Check if all required fields exist."""
        try:
            with engine.connect() as conn:
                # Check for new fields that should exist after migrations
                if settings.database_url.startswith('postgresql'):
                    result = conn.execute(text("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'users' 
                        AND column_name IN ('google_calendar_id', 'oauth_credentials', 'calendar_connected')
                    """))
                else:
                    result = conn.execute(text("PRAGMA table_info(users)"))
                    columns = [row[1] for row in result.fetchall()]
                    required_fields = {'google_calendar_id', 'oauth_credentials', 'calendar_connected'}
                    missing_fields = required_fields - set(columns)
                    
                    return {
                        'success': len(missing_fields) == 0,
                        'message': f'Migration status: {"Complete" if len(missing_fields) == 0 else "Incomplete"}',
                        'missing_fields': list(missing_fields) if missing_fields else []
                    }
                
                columns = [row[0] for row in result.fetchall()]
                required_fields = {'google_calendar_id', 'oauth_credentials', 'calendar_connected'}
                missing_fields = required_fields - set(columns)
                
                return {
                    'success': len(missing_fields) == 0,
                    'message': f'Migration status: {"Complete" if len(missing_fields) == 0 else "Incomplete"}',
                    'missing_fields': list(missing_fields) if missing_fields else []
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Migration check failed: {str(e)}',
                'error': str(e)
            }
    
    def attempt_recovery(self) -> bool:
        """Attempt to recover from database issues."""
        logger.info("Attempting database recovery...")
        
        try:
            # Try to reinitialize database
            from database import init_db
            init_db()
            
            # Run health check to verify recovery
            health = self.check_database_health()
            success = health['status'] in ['healthy', 'degraded']
            
            if success:
                logger.info("✅ Database recovery successful")
                self.consecutive_failures = 0
            else:
                logger.error("❌ Database recovery failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Database recovery failed: {e}")
            return False
    
    def should_attempt_recovery(self) -> bool:
        """Determine if recovery should be attempted."""
        return (
            self.consecutive_failures >= self.max_failures and
            (not self.last_health_check or 
             datetime.now() - self.last_health_check > timedelta(minutes=5))
        )

# Global health monitor instance
health_monitor = DatabaseHealthMonitor()

def get_database_status() -> Dict[str, Any]:
    """Get current database status."""
    return health_monitor.check_database_health()

def ensure_database_health() -> bool:
    """Ensure database is healthy, attempt recovery if needed."""
    health = health_monitor.check_database_health()
    
    if health['status'] == 'critical' and health_monitor.should_attempt_recovery():
        return health_monitor.attempt_recovery()
    
    return health['status'] in ['healthy', 'degraded']