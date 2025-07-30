#!/usr/bin/env python3
"""
Migration script to fix PostgreSQL enum values compatibility.
This script ensures that PostgreSQL enum types match the Python enum definitions.
"""

import asyncio
import logging
from sqlalchemy import create_engine, text
from src.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_enum_migration():
    """Fix PostgreSQL enum types to match Python definitions."""
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Check if we're using PostgreSQL
            if not settings.database_url.startswith('postgresql'):
                logger.info("Not using PostgreSQL, skipping enum migration")
                return
            
            logger.info("Starting enum migration for PostgreSQL...")
            
            # Begin transaction
            trans = conn.begin()
            
            try:
                # Drop existing enum types if they exist (recreate them)
                logger.info("Dropping existing enum types...")
                conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE;"))
                conn.execute(text("DROP TYPE IF EXISTS userstatus CASCADE;"))
                conn.execute(text("DROP TYPE IF EXISTS meetingstatus CASCADE;"))
                conn.execute(text("DROP TYPE IF EXISTS department CASCADE;"))
                
                # Recreate enum types with correct values
                logger.info("Creating enum types...")
                conn.execute(text("CREATE TYPE userrole AS ENUM ('owner', 'manager', 'pending');"))
                conn.execute(text("CREATE TYPE userstatus AS ENUM ('active', 'vacation', 'sick_leave', 'business_trip', 'deleted');"))
                conn.execute(text("CREATE TYPE meetingstatus AS ENUM ('scheduled', 'completed', 'cancelled', 'no_show');"))
                conn.execute(text("CREATE TYPE department AS ENUM ('Фарм отдел', 'Фин отдел', 'HR отдел', 'Тех отдел', 'ИТ отдел', 'Биздев отдел', 'Геймдев проект');"))
                
                # Update existing tables to use new enum types
                logger.info("Updating table columns...")
                
                # Check if tables exist first
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'users'
                """))
                
                if result.fetchone():
                    # Alter existing columns to use new enum types
                    conn.execute(text("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::text::userrole;"))
                    conn.execute(text("ALTER TABLE users ALTER COLUMN status TYPE userstatus USING status::text::userstatus;"))
                    conn.execute(text("ALTER TABLE users ALTER COLUMN department TYPE department USING department::text::department;"))
                
                # Check if meetings table exists
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'meetings'
                """))
                
                if result.fetchone():
                    conn.execute(text("ALTER TABLE meetings ALTER COLUMN status TYPE meetingstatus USING status::text::meetingstatus;"))
                
                # Commit transaction
                trans.commit()
                logger.info("✅ Enum migration completed successfully!")
                
            except Exception as e:
                # Rollback transaction on error
                trans.rollback()
                logger.error(f"❌ Migration failed, rolling back: {e}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

if __name__ == "__main__":
    fix_enum_migration()