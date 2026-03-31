import asyncpg
import logging
from config import DATABASE_URL

logger = logging.getLogger(__name__)

async def init_db():
    if not DATABASE_URL:
        logger.error("Нет DATABASE_URL. Пропускаю инициализацию БД.")
        return

    try:
        # Для Supabase иногда нужно добавлять sslmode=require
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Создаем основные таблицы
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                nickname TEXT,
                role TEXT DEFAULT 'player',
                reputation INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS warehouse (
                id SERIAL PRIMARY KEY,
                resource_name TEXT UNIQUE,
                count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                resource_type TEXT,
                target_count INTEGER,
                deadline TIMESTAMP
            );
        ''')
        await conn.close()
        logger.info("✅ База данных готова.")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        raise e
