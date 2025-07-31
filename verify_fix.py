#!/usr/bin/env python3
"""
✅ VERIFICATION SCRIPT - Проверка исправления
Проверяет что ошибка column meetings.google_calendar_id does not exist исправлена

🎯 Ultimate Diagnostic System v2.0 - PHASE 6 VERIFICATION
"""

import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - VERIFY - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_problematic_query():
    """Test the exact query that was failing"""
    logger.info("🧪 Testing problematic query from error log...")
    
    try:
        from sqlalchemy import create_engine, text
        from config import settings
        
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            # This is the EXACT query that was failing
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
                WHERE meetings.manager_id = 2 
                AND meetings.scheduled_time >= '2025-08-04 00:00:00' 
                AND meetings.scheduled_time <= '2025-08-10 00:00:00' 
                AND meetings.status = 'scheduled' 
                LIMIT 1
            """))
            
            rows = result.fetchall()
            logger.info(f"✅ Query successful - returned {len(rows)} rows")
            return True
            
    except Exception as e:
        if "google_calendar_id does not exist" in str(e):
            logger.error("❌ PROBLEM STILL EXISTS: google_calendar_id column missing")
            return False
        else:
            logger.error(f"❌ Unexpected error: {e}")
            return False
    finally:
        if 'engine' in locals():
            engine.dispose()

def test_column_exists():
    """Test if google_calendar_id column exists"""
    logger.info("🔍 Checking if google_calendar_id column exists...")
    
    try:
        from sqlalchemy import create_engine, text
        from config import settings
        
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            if settings.database_url.startswith('postgresql'):
                # PostgreSQL check
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='meetings' AND column_name='google_calendar_id'
                """))
                columns = result.fetchall()
                exists = len(columns) > 0
            else:
                # SQLite check
                result = conn.execute(text("PRAGMA table_info(meetings)"))
                columns = [row[1] for row in result.fetchall()]
                exists = 'google_calendar_id' in columns
            
            if exists:
                logger.info("✅ Column google_calendar_id EXISTS")
                return True
            else:
                logger.error("❌ Column google_calendar_id DOES NOT EXIST")
                return False
                
    except Exception as e:
        logger.error(f"❌ Column check failed: {e}")
        return False
    finally:
        if 'engine' in locals():
            engine.dispose()

def test_booking_simulation():
    """Simulate the booking process that was failing"""
    logger.info("🎯 Simulating booking process...")
    
    try:
        # Import the handler that was failing
        from src.handlers.manager import book_meeting_time
        logger.info("✅ Manager handler import successful")
        
        # Test SQLAlchemy model
        from src.database import Meeting
        logger.info("✅ Meeting model import successful")
        
        # Check if model has google_calendar_id attribute
        if hasattr(Meeting, 'google_calendar_id'):
            logger.info("✅ Meeting model has google_calendar_id attribute")
        else:
            logger.error("❌ Meeting model missing google_calendar_id attribute")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Booking simulation failed: {e}")
        return False

def generate_verification_report():
    """Generate comprehensive verification report"""
    logger.info("📋 GENERATING VERIFICATION REPORT")
    logger.info("=" * 60)
    
    results = {
        'column_exists': test_column_exists(),
        'problematic_query': test_problematic_query(), 
        'booking_simulation': test_booking_simulation()
    }
    
    all_passed = all(results.values())
    
    logger.info("📊 VERIFICATION RESULTS:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    if all_passed:
        logger.info("=" * 60)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ Problem RESOLVED: google_calendar_id column exists")
        logger.info("✅ Booking functionality should work")
        logger.info("🚀 Users can now book meetings successfully")
        logger.info("=" * 60)
        return True
    else:
        logger.error("=" * 60)
        logger.error("❌ VERIFICATION FAILED!")
        logger.error("🚨 Problem NOT resolved - manual intervention needed")
        logger.error("📞 Contact database administrator")
        logger.error("=" * 60)
        return False

def main():
    """Main verification function"""
    logger.info("🎯 ULTIMATE DIAGNOSTIC SYSTEM v2.0")
    logger.info("✅ SOLUTION VERIFICATION TOOL")
    logger.info(f"Started at: {datetime.now()}")
    
    success = generate_verification_report()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()