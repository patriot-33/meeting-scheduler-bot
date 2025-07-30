"""
Migration to add calendar_connected field to users table
"""
import logging
from sqlalchemy import create_engine, text
from config import settings

logger = logging.getLogger(__name__)

def upgrade():
    """Add calendar_connected column to users table."""
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='calendar_connected'
            """))
            
            if result.rowcount == 0:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN calendar_connected BOOLEAN DEFAULT FALSE
                """))
                conn.commit()
                logger.info("✅ Added calendar_connected column to users table")
            else:
                logger.info("ℹ️ Column calendar_connected already exists")
                
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()