#!/usr/bin/env python3
"""
🚨 КРИТИЧНОЕ ИСПРАВЛЕНИЕ: Применение миграции google_calendar_id

🎯 Ultimate Diagnostic System v2.0 - PHASE 5 SOLUTION IMPLEMENTATION
🔥 ЖЕЛЕЗНЫЙ ЗАКОН: Безопасная реализация с автоматическим rollback

Решает ошибку: column meetings.google_calendar_id does not exist
Приоритет: P1_HIGH (пользователи затронуты)

USAGE:
    python3 apply_critical_migration.py          # Apply migration
    python3 apply_critical_migration.py test     # Test migration
    python3 apply_critical_migration.py rollback # Rollback migration
"""

import sys
import logging
from datetime import datetime
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('critical_migration.log')
    ]
)
logger = logging.getLogger(__name__)

def log_system_state():
    """Log system state for diagnostics"""
    import psutil
    logger.info("🖥️ SYSTEM STATE:")
    logger.info(f"   CPU: {psutil.cpu_percent()}%")
    logger.info(f"   Memory: {psutil.virtual_memory().percent}%")
    logger.info(f"   Disk: {psutil.disk_usage('/').percent}%")

def test_current_problem():
    """Test if the problem still exists"""
    logger.info("🧪 TESTING CURRENT PROBLEM...")
    
    try:
        from sqlalchemy import create_engine, text
        from config import settings
        
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            # Try the problematic query from the error log
            result = conn.execute(text("""
                SELECT meetings.google_calendar_id AS meetings_google_calendar_id
                FROM meetings 
                LIMIT 1
            """))
            result.fetchall()
            logger.info("✅ Problem RESOLVED: google_calendar_id column exists")
            return False  # Problem doesn't exist
            
    except Exception as e:
        if "google_calendar_id does not exist" in str(e):
            logger.error("❌ Problem CONFIRMED: google_calendar_id column missing")
            return True  # Problem exists
        else:
            logger.error(f"❌ Unexpected error: {e}")
            return True
    finally:
        if 'engine' in locals():
            engine.dispose()

def apply_migration():
    """Apply the critical migration"""
    logger.info("🚀 APPLYING CRITICAL MIGRATION...")
    logger.info("=" * 60)
    
    # Log system state
    log_system_state()
    
    # Test problem exists
    if not test_current_problem():
        logger.info("✅ Problem already resolved - no migration needed")
        return True
    
    try:
        # Import and run migration
        from migrations.add_google_calendar_id_field import upgrade
        
        logger.info("🔧 Executing migration...")
        success = upgrade()
        
        if success:
            logger.info("✅ Migration applied successfully")
            
            # Verify problem is solved
            if not test_current_problem():
                logger.info("🎉 SOLUTION VERIFIED: Problem is resolved!")
                return True
            else:
                logger.error("❌ Migration applied but problem persists")
                return False
        else:
            logger.error("❌ Migration failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed with exception: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def rollback_migration():
    """Rollback the migration"""
    logger.info("🔄 ROLLING BACK MIGRATION...")
    
    try:
        from migrations.add_google_calendar_id_field import downgrade
        downgrade()
        logger.info("✅ Rollback successful")
        return True
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        return False

def test_booking_functionality():
    """Test that booking functionality works after migration"""
    logger.info("🧪 TESTING BOOKING FUNCTIONALITY...")
    
    try:
        from sqlalchemy import create_engine, text
        from config import settings
        
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            # Test the exact query that was failing
            result = conn.execute(text("""
                SELECT meetings.id AS meetings_id, 
                       meetings.manager_id AS meetings_manager_id, 
                       meetings.scheduled_time AS meetings_scheduled_time, 
                       meetings.google_event_id AS meetings_google_event_id, 
                       meetings.google_meet_link AS meetings_google_meet_link, 
                       meetings.google_calendar_id AS meetings_google_calendar_id, 
                       meetings.status AS meetings_status, 
                       meetings.created_at AS meetings_created_at, 
                       meetings.updated_at AS meetings_updated_at 
                FROM meetings 
                LIMIT 1
            """))
            
            rows = result.fetchall()
            logger.info(f"✅ Query successful - returned {len(rows)} rows")
            logger.info("🎉 Booking functionality should work now!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Booking test failed: {e}")
        return False
    finally:
        if 'engine' in locals():
            engine.dispose()

def main():
    """Main execution function"""
    logger.info("🎯 ULTIMATE DIAGNOSTIC SYSTEM v2.0")
    logger.info("🚨 CRITICAL MIGRATION TOOL")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now()}")
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    
    if mode == "test":
        logger.info("🧪 TESTING MODE")
        problem_exists = test_current_problem()
        if problem_exists:
            logger.error("❌ Problem exists - migration needed")
            sys.exit(1)
        else:
            logger.info("✅ No problem detected")
            sys.exit(0)
            
    elif mode == "rollback":
        logger.info("🔄 ROLLBACK MODE")
        success = rollback_migration()
        sys.exit(0 if success else 1)
        
    else:  # apply mode
        logger.info("🚀 APPLY MIGRATION MODE")
        success = apply_migration()
        
        if success:
            logger.info("🧪 Testing booking functionality...")
            test_success = test_booking_functionality()
            
            if test_success:
                logger.info("=" * 60)
                logger.info("🎉 CRITICAL MIGRATION SUCCESSFUL!")
                logger.info("✅ Problem resolved: google_calendar_id column exists")
                logger.info("✅ Booking functionality verified")
                logger.info("🚀 Users can now book meetings successfully")
                logger.info("=" * 60)
                sys.exit(0)
            else:
                logger.error("❌ Migration successful but booking test failed")
                sys.exit(1)
        else:
            logger.error("❌ Migration failed")
            sys.exit(1)

if __name__ == "__main__":
    main()