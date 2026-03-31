import aiosqlite
from config import DB_PATH


import aiosqlite
from config import DB_PATH # Убедись, что путь к БД импортируется

async def get_or_create_user(telegram_id, username=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # 1. Сначала ищем пользователя
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            user = await cursor.fetchone()
            if user:
                return user # Если нашли, просто возвращаем его
        
        # 2. Если не нашли, создаем нового
        await db.execute(
            "INSERT INTO users (telegram_id, username, role, reputation) VALUES (?, ?, ?, ?)",
            (telegram_id, username, 'player', 0)
        )
        await db.commit()
        
        # Возвращаем созданного пользователя
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            return await cursor.fetchone()
)
        )
        await db.commit()
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            user = await cursor.fetchone()
        return dict(user)


async def update_nickname(telegram_id: int, nickname: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET nickname = ? WHERE telegram_id = ?",
            (nickname, telegram_id),
        )
        await db.commit()


async def add_reputation(telegram_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET reputation = reputation + ? WHERE telegram_id = ?",
            (amount, telegram_id),
        )
        await db.commit()


async def get_all_users() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY reputation DESC") as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def get_user_warns(telegram_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        user = await _get_user(db, telegram_id)
        if not user:
            return 0
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM warns WHERE user_id = ?", (user["id"],)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0]


async def add_warn(telegram_id: int, reason: str = "") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
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
            return row[0]


async def _get_user(db, telegram_id: int):
    db.row_factory = aiosqlite.Row
    async with db.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None
