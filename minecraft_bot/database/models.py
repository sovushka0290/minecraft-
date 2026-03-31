import asyncpg
import logging
from config import DATABASE_URL

# Настройка логов, чтобы видеть, если что-то пойдет не так
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    """Инициализирует структуру таблиц в PostgreSQL (Supabase/Render)"""
    if not DATABASE_URL:
        logger.error("DATABASE_URL не найден! Проверь настройки Environment на Render.")
        return

    try:
        conn = await asyncpg.connect(DATABASE_URL)
        logger.info("Подключение к PostgreSQL установлено. Создаю таблицы...")

        # 1. Таблица пользователей
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

        # 2. Таблица задач
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                resource_type TEXT,
                target_count INTEGER,
                deadline TIMESTAMP
            )
        ''')

        # 3. Прогресс игроков по задачам
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'in_progress'
            )
        ''')

        # 4. Склад ресурсов
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS warehouse (
                id SERIAL PRIMARY KEY,
                resource_name TEXT UNIQUE,
                count INTEGER DEFAULT 0
            )
        ''')

        # 5. Отчеты игроков
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                photo_id TEXT,
                count INTEGER,
                status TEXT DEFAULT 'pending', -- pending, approved, rejected
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 6. Варны (предупреждения)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS warns (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 7. Логи событий (для истории)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                event_type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        logger.info("✅ Все таблицы успешно созданы или уже существуют.")
        await conn.close()

    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
        raise e
