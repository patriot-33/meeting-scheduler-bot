"""
🚨 КРИТИЧНАЯ МИГРАЦИЯ: Добавление google_calendar_id в таблицу meetings
Решает ошибку: column meetings.google_calendar_id does not exist

PHASE 5 - SOLUTION IMPLEMENTATION of Ultimate Diagnostic System v2.0
🔥 ЖЕЛЕЗНЫЙ ЗАКОН: Безопасная реализация с rollback возможностями
"""
import logging
from sqlalchemy import create_engine, text
from config import settings

logger = logging.getLogger(__name__)

def column_exists(conn, table_name, column_name):
    """Check if column exists in database-agnostic way."""
    try:
        if settings.database_url.startswith('postgresql'):
            # PostgreSQL: use information_schema
            result = conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='{table_name}' AND column_name='{column_name}'
            """))
            return len(result.fetchall()) > 0
        else:
            # SQLite: use PRAGMA table_info
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]
            return column_name in columns
    except Exception as e:
        logger.warning(f"Could not check column existence: {e}")
        return False

def backup_current_schema(conn):
    """Create backup of current schema information"""
    try:
        logger.info("📋 Creating schema backup...")
        if settings.database_url.startswith('postgresql'):
            # PostgreSQL schema backup
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name='meetings'
                ORDER BY ordinal_position
            """))
            schema_backup = result.fetchall()
            logger.info(f"📋 Schema backup created: {len(schema_backup)} columns")
            return schema_backup
        else:
            # SQLite schema backup
            result = conn.execute(text("PRAGMA table_info(meetings)"))
            schema_backup = result.fetchall()
            logger.info(f"📋 Schema backup created: {len(schema_backup)} columns")
            return schema_backup
    except Exception as e:
        logger.error(f"❌ Schema backup failed: {e}")
        return None

def verify_migration_success(conn):
    """Verify that migration was successful"""
    try:
        # Test that we can SELECT the new column
        result = conn.execute(text("SELECT google_calendar_id FROM meetings LIMIT 1"))
        result.fetchall()  # This will fail if column doesn't exist
        logger.info("✅ Migration verification successful")
        return True
    except Exception as e:
        logger.error(f"❌ Migration verification failed: {e}")
        return False

def upgrade():
    """Add google_calendar_id column to meetings table with bulletproof safety."""
    logger.info("🚀 STARTING CRITICAL MIGRATION: google_calendar_id field")
    logger.info("🎯 Diagnostic System v2.0 - Safe Implementation Phase")
    
    engine = create_engine(settings.database_url)
    schema_backup = None
    
    try:
        with engine.connect() as conn:
            # STEP 1: Create backup
            schema_backup = backup_current_schema(conn)
            
            # STEP 2: Check if column already exists
            if column_exists(conn, 'meetings', 'google_calendar_id'):
                logger.info("ℹ️ Column google_calendar_id already exists - no migration needed")
                return True
            
            logger.info("🔧 Column google_calendar_id does not exist - adding...")
            
            # STEP 3: Add the column with database-specific syntax
            if settings.database_url.startswith('postgresql'):
                # PostgreSQL
                logger.info("🐘 Using PostgreSQL syntax")
                conn.execute(text("""
                    ALTER TABLE meetings 
                    ADD COLUMN google_calendar_id VARCHAR(255)
                """))
            else:
                # SQLite
                logger.info("🗃️ Using SQLite syntax")
                conn.execute(text("""
                    ALTER TABLE meetings 
                    ADD COLUMN google_calendar_id VARCHAR(255)
                """))
            
            # STEP 4: Commit transaction
            conn.commit()
            logger.info("💾 Migration transaction committed")
            
            # STEP 5: Verify migration success
            if verify_migration_success(conn):
                logger.info("✅ MIGRATION SUCCESSFUL: google_calendar_id column added")
                logger.info("🎉 Problem resolved: meetings.google_calendar_id now exists")
                return True
            else:
                raise Exception("Migration verification failed")
                
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        logger.error("🔄 Attempting rollback strategies...")
        
        # Try alternative approach
        try:
            with engine.connect() as conn:
                # Check if we need to rollback
                if schema_backup:
                    logger.info("📋 Schema backup available for reference")
                
                # Try a different syntax
                logger.info("🔄 Trying alternative migration syntax...")
                if settings.database_url.startswith('postgresql'):
                    # Try with explicit NULL constraint
                    conn.execute(text("""
                        ALTER TABLE meetings 
                        ADD COLUMN IF NOT EXISTS google_calendar_id VARCHAR(255) NULL
                    """))
                else:
                    # For SQLite, column might already exist
                    conn.execute(text("""
                        ALTER TABLE meetings 
                        ADD COLUMN google_calendar_id VARCHAR(255)
                    """))
                
                conn.commit()
                
                if verify_migration_success(conn):
                    logger.info("✅ Fallback migration successful")
                    return True
                else:
                    raise Exception("Fallback migration verification failed")
                    
        except Exception as fallback_error:
            logger.error(f"❌ Fallback migration also failed: {fallback_error}")
            logger.error("🚨 CRITICAL: Manual intervention required")
            logger.error("📞 Contact database administrator immediately")
            raise
            
    finally:
        engine.dispose()
        logger.info("🔌 Database connection disposed")

def downgrade():
    """Remove google_calendar_id column (rollback migration)"""
    logger.info("🔄 ROLLBACK: Removing google_calendar_id column")
    
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            if column_exists(conn, 'meetings', 'google_calendar_id'):
                logger.info("🗑️ Dropping google_calendar_id column...")
                
                if settings.database_url.startswith('postgresql'):
                    conn.execute(text("""
                        ALTER TABLE meetings 
                        DROP COLUMN google_calendar_id
                    """))
                else:
                    # SQLite doesn't support DROP COLUMN easily
                    logger.error("❌ SQLite doesn't support DROP COLUMN - manual intervention needed")
                    raise Exception("Cannot rollback in SQLite")
                
                conn.commit()
                logger.info("✅ Rollback successful")
            else:
                logger.info("ℹ️ Column doesn't exist - rollback not needed")
                
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()