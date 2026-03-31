import aiosqlite
from config import DB_PATH

import asyncpg
from config import DATABASE_URL

async def get_or_create_user(telegram_id: int, username: str = None):
    # Подключаемся к Postgres
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # 1. Ищем юзера
        user = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
        
        if user:
            return dict(user)
        
        # 2. Если нет — создаем
        await conn.execute(
            "INSERT INTO users (telegram_id, username, role, reputation) VALUES ($1, $2, $3, $4) ON CONFLICT (telegram_id) DO NOTHING",
            telegram_id, username, 'player', 0
        )
        
        # Получаем созданного
        user = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
        return dict(user)
    finally:
        await conn.close()
async def add_reputation(telegram_id: int, amount: int):
    """Добавляет или отнимает репутацию."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET reputation = reputation + ? WHERE telegram_id = ?",
            (amount, telegram_id),
        )
        await db.commit()

async def get_all_users() -> list:
    """Возвращает список всех игроков, отсортированный по репутации."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY reputation DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_user_warns(telegram_id: int) -> int:
    """Считает количество варнов пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        user = await _get_user(db, telegram_id)
        if not user:
            return 0
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM warns WHERE user_id = ?", (user["id"],)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def add_warn(telegram_id: int, reason: str = "") -> int:
    """Добавляет варн и возвращает их общее количество."""
    async with aiosqlite.connect(DB_PATH) as db:
        user = await _get_user(db, telegram_id)
        if not user:
            return 0
        await db.execute(
            "INSERT INTO warns (user_id, reason) VALUES (?, ?)",
            (user["id"], reason),
        )
        await db.commit()
        
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM warns WHERE user_id = ?", (user["id"],)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def _get_user(db, telegram_id: int):
    """Вспомогательная функция для получения юзера внутри открытого соединения."""
    db.row_factory = aiosqlite.Row
    async with db.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None
