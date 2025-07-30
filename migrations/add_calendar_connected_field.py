"""
Migration to add calendar_connected field to users table
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

def upgrade():
    """Add calendar_connected column to users table with bulletproof compatibility."""
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists (database-agnostic)
            if not column_exists(conn, 'users', 'calendar_connected'):
                logger.info("Adding calendar_connected column to users table...")
                
                # Add the column with database-specific syntax
                if settings.database_url.startswith('postgresql'):
                    # PostgreSQL
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN calendar_connected BOOLEAN DEFAULT FALSE
                    """))
                else:
                    # SQLite
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN calendar_connected BOOLEAN DEFAULT 0
                    """))
                
                conn.commit()
                logger.info("✅ Added calendar_connected column to users table")
            else:
                logger.info("ℹ️ Column calendar_connected already exists")
                
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        # Try alternative approach
        try:
            with engine.connect() as conn:
                # Force add column (will fail gracefully if exists)
                conn.execute(text("ALTER TABLE users ADD COLUMN calendar_connected BOOLEAN DEFAULT FALSE"))
                conn.commit()
                logger.info("✅ Fallback migration successful")
        except Exception as fallback_error:
            logger.error(f"❌ Fallback migration also failed: {fallback_error}")
            raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()