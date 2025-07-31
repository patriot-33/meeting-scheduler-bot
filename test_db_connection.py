#!/usr/bin/env python3
"""
🔍 ДИАГНОСТИЧЕСКИЙ СКРИПТ: Тестирование подключения к PostgreSQL
"""

import logging
import sys
import psycopg2
from sqlalchemy import create_engine, text
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# База данных на Render.com
DATABASE_URL = "postgresql://meeting_bot:1ZbNJ4bHtcL3Ji8i8pmfGchOVxx5v94r@dpg-d24ersali9vc73cnfsu0-a.frankfurt-postgres.render.com/meeting_scheduler"

def test_psycopg2_connection():
    """Тест 1: Прямое подключение через psycopg2"""
    logger.info("🧪 ТЕСТ 1: Проверка подключения через psycopg2")
    try:
        # Парсим URL для psycopg2
        import urllib.parse
        url = urllib.parse.urlparse(DATABASE_URL)
        
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port or 5432,
            database=url.path[1:],  # Убираем слеш
            user=url.username,
            password=url.password,
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"✅ Подключение успешно! PostgreSQL версия: {version[0]}")
        
        # Проверяем таблицы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        logger.info(f"📊 Найдено таблиц: {len(tables)}")
        for table in tables:
            logger.info(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения через psycopg2: {type(e).__name__}: {e}")
        return False

def test_sqlalchemy_connection():
    """Тест 2: Подключение через SQLAlchemy"""
    logger.info("\n🧪 ТЕСТ 2: Проверка подключения через SQLAlchemy")
    try:
        engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Подключение через SQLAlchemy успешно!")
            
            # Проверяем структуру таблицы users
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            if columns:
                logger.info("📋 Структура таблицы 'users':")
                for col in columns:
                    logger.info(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")
            else:
                logger.warning("⚠️ Таблица 'users' не найдена!")
            
            # Проверяем количество записей
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            logger.info(f"👥 Количество пользователей: {count}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения через SQLAlchemy: {type(e).__name__}: {e}")
        return False

def test_database_health():
    """Тест 3: Проверка здоровья базы данных"""
    logger.info("\n🧪 ТЕСТ 3: Проверка здоровья базы данных")
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        
        with engine.connect() as conn:
            # Проверяем все таблицы и их размеры
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """))
            
            tables = result.fetchall()
            logger.info("📊 Размеры таблиц:")
            for schema, table, size in tables:
                logger.info(f"   - {table}: {size}")
            
            # Проверяем активные подключения
            result = conn.execute(text("""
                SELECT count(*) 
                FROM pg_stat_activity 
                WHERE datname = current_database();
            """))
            connections = result.scalar()
            logger.info(f"🔌 Активных подключений: {connections}")
            
            # Проверяем последние встречи
            result = conn.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled,
                       COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                       COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled
                FROM meetings;
            """))
            
            stats = result.fetchone()
            logger.info(f"📅 Статистика встреч:")
            logger.info(f"   - Всего: {stats[0]}")
            logger.info(f"   - Запланировано: {stats[1]}")
            logger.info(f"   - Завершено: {stats[2]}")
            logger.info(f"   - Отменено: {stats[3]}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки здоровья БД: {type(e).__name__}: {e}")
        return False

def main():
    logger.info("🚀 НАЧАЛО ДИАГНОСТИКИ БАЗЫ ДАННЫХ")
    logger.info(f"📍 URL: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('://')[1], '***:***')}")
    logger.info(f"🕐 Время: {datetime.now()}")
    
    results = []
    
    # Выполняем тесты
    results.append(("psycopg2", test_psycopg2_connection()))
    results.append(("SQLAlchemy", test_sqlalchemy_connection()))
    results.append(("Health Check", test_database_health()))
    
    # Итоги
    logger.info("\n📊 ИТОГИ ДИАГНОСТИКИ:")
    success_count = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\n🎯 Результат: {success_count}/{len(results)} тестов пройдено")
    
    if success_count == len(results):
        logger.info("✅ База данных работает корректно!")
        return 0
    else:
        logger.error("❌ Обнаружены проблемы с базой данных!")
        return 1

if __name__ == "__main__":
    sys.exit(main())