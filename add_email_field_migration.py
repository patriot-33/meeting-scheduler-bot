#!/usr/bin/env python3
"""
Миграция для добавления поля email в таблицу users
"""
import logging
from sqlalchemy import create_engine, text
from src.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_email_field():
    """Добавить поле email в таблицу users если его нет"""
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Проверяем, существует ли колонка email
            if settings.database_url.startswith('postgresql'):
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='email'
                """))
            else:  # SQLite
                result = conn.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result.fetchall()]
                result = columns if 'email' in columns else []
            
            if not result.fetchall():
                logger.info("Добавляем поле email в таблицу users...")
                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
                conn.commit()
                logger.info("✅ Поле email успешно добавлено")
            else:
                logger.info("✅ Поле email уже существует")
                
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        raise

if __name__ == '__main__':
    add_email_field()