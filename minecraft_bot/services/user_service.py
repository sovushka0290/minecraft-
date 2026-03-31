import aiosqlite
from config import DB_PATH

async def get_or_create_user(telegram_id: int, username: str = None):
    """Получает пользователя из базы или создает нового, если его нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # 1. Сначала ищем пользователя
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            user = await cursor.fetchone()
            if user:
                return dict(user) # Если нашли, возвращаем как словарь
        
        # 2. Если не нашли, создаем нового (INSERT OR IGNORE на всякий случай)
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username, role, reputation) VALUES (?, ?, ?, ?)",
            (telegram_id, username, 'player', 0)
        )
        await db.commit()
        
        # 3. Возвращаем только что созданного пользователя
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            user = await cursor.fetchone()
            return dict(user) if user else None

async def update_nickname(telegram_id: int, nickname: str):
    """Обновляет никнейм игрока."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET nickname = ? WHERE telegram_id = ?",
            (nickname, telegram_id),
        )
        await db.commit()

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
