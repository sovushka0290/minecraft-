import asyncpg
from config import DATABASE_URL

async def init_db():
    """Создает таблицы в PostgreSQL, если их еще нет."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Таблица пользователей
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                nickname TEXT,
                role TEXT DEFAULT 'player',
                reputation INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица задач
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                resource_type TEXT,
                target_count INTEGER,
                deadline TIMESTAMP
            )
        ''')
        
        # Таблица склада
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS warehouse (
                id SERIAL PRIMARY KEY,
                resource_name TEXT UNIQUE,
                count INTEGER DEFAULT 0
            )
        ''')
        
        # Добавь остальные таблицы (warns, reports) по аналогии...
        
    finally:
        await conn.close()
