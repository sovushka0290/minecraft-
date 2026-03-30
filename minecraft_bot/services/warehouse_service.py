import aiosqlite
from config import DB_PATH


async def add_to_warehouse(item_name: str, quantity: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO warehouse (item_name, quantity)
            VALUES (?, ?)
            ON CONFLICT(item_name) DO UPDATE
            SET quantity = quantity + excluded.quantity,
                updated_at = CURRENT_TIMESTAMP
        """, (item_name, quantity))
        await db.commit()


async def get_warehouse() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM warehouse ORDER BY item_name ASC"
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def set_warehouse_item(item_name: str, quantity: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO warehouse (item_name, quantity)
            VALUES (?, ?)
            ON CONFLICT(item_name) DO UPDATE
            SET quantity = excluded.quantity,
                updated_at = CURRENT_TIMESTAMP
        """, (item_name, quantity))
        await db.commit()
