#!/usr/bin/env python3
"""
Hotfix for enum DataError. Forcefully recreates database schema.
"""

import os
import logging
from sqlalchemy import create_engine, text
from src.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hotfix_enum_database():
    """Hotfix: Drop and recreate database schema with correct enums."""
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            if not settings.database_url.startswith('postgresql'):
                logger.info("Not PostgreSQL, skipping hotfix")
                return
                
            logger.info("🔥 HOTFIX: Forcefully recreating database schema...")
            
            # Begin transaction
            trans = conn.begin()
            
            try:
                # Drop all tables (this will also drop enum dependencies)
                logger.info("Dropping all existing tables...")
                conn.execute(text("DROP TABLE IF EXISTS reminders CASCADE;"))
                conn.execute(text("DROP TABLE IF EXISTS statistics CASCADE;"))
                conn.execute(text("DROP TABLE IF EXISTS owner_blocked_time CASCADE;"))
                conn.execute(text("DROP TABLE IF EXISTS owner_availability CASCADE;"))
                conn.execute(text("DROP TABLE IF EXISTS meetings CASCADE;"))
                conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
                
                # Drop all enum types
                logger.info("Dropping all enum types...")
                conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE;"))
                conn.execute(text("DROP TYPE IF EXISTS userstatus CASCADE;"))
                conn.execute(text("DROP TYPE IF EXISTS meetingstatus CASCADE;"))
                conn.execute(text("DROP TYPE IF EXISTS department CASCADE;"))
                
                # Create enum types with correct lowercase values
                logger.info("Creating enum types with correct values...")
                conn.execute(text("CREATE TYPE userrole AS ENUM ('owner', 'manager', 'pending');"))
                conn.execute(text("CREATE TYPE userstatus AS ENUM ('active', 'vacation', 'sick_leave', 'business_trip', 'deleted');"))
                conn.execute(text("CREATE TYPE meetingstatus AS ENUM ('scheduled', 'completed', 'cancelled', 'no_show');"))
                conn.execute(text("CREATE TYPE department AS ENUM ('Фарм отдел', 'Фин отдел', 'HR отдел', 'Тех отдел', 'ИТ отдел', 'Биздев отдел', 'Геймдев проект');"))
                
                trans.commit()
                logger.info("✅ Database schema reset completed!")
                
                # Now recreate tables using SQLAlchemy
                logger.info("Recreating tables using SQLAlchemy...")
                from src.database import Base, engine as db_engine
                Base.metadata.create_all(bind=db_engine)
                logger.info("✅ Tables recreated successfully!")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Hotfix failed, rolling back: {e}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Hotfix failed: {e}")
        raise

if __name__ == "__main__":
    hotfix_enum_database()