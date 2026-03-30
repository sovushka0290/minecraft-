import aiosqlite
from config import DB_PATH
from services.warehouse_service import add_to_warehouse
from services.user_service import add_reputation


def progress_bar(current: int, required: int, length: int = 10) -> str:
    if required == 0:
        return "█" * length
    filled = int(length * current / required)
    filled = min(filled, length)
    bar = "█" * filled + "░" * (length - filled)
    pct = int(100 * current / required)
    return f"{bar} {pct}%"


async def get_user_tasks(telegram_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as c:
            row = await c.fetchone()
        if not row:
            return []
        user_id = row["id"]
        async with db.execute("""
            SELECT t.id, t.title, t.task_type, t.required_amount, t.deadline, t.status,
                   ut.progress, ut.status as ut_status
            FROM tasks t
            JOIN user_tasks ut ON ut.task_id = t.id
            WHERE ut.user_id = ? AND t.status = 'active'
            ORDER BY t.deadline ASC
        """, (user_id,)) as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def get_active_tasks() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tasks WHERE status = 'active' ORDER BY deadline ASC"
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def get_task(task_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as c:
            row = await c.fetchone()
            return dict(row) if row else None


async def create_task(title: str, task_type: str, amount: int,
                      deadline: str, assign_to: str = "all") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO tasks (title, task_type, required_amount, deadline, assigned_to)
            VALUES (?, ?, ?, ?, ?)
        """, (title, task_type, amount, deadline, assign_to))
        task_id = cursor.lastrowid
        await db.commit()

        # Назначить задачу игрокам
        if assign_to == "all":
            async with db.execute("SELECT id FROM users") as c:
                users = await c.fetchall()
            for u in users:
                await db.execute(
                    "INSERT INTO user_tasks (user_id, task_id) VALUES (?, ?)",
                    (u[0], task_id),
                )
        else:
            # assign_to = "telegram_id1,telegram_id2"
            for tg_id in assign_to.split(","):
                async with db.execute(
                    "SELECT id FROM users WHERE telegram_id = ?", (int(tg_id.strip()),)
                ) as c:
                    u = await c.fetchone()
                if u:
                    await db.execute(
                        "INSERT INTO user_tasks (user_id, task_id) VALUES (?, ?)",
                        (u[0], task_id),
                    )
        await db.commit()
        return task_id


async def delete_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tasks SET status = 'deleted' WHERE id = ?", (task_id,))
        await db.commit()


async def save_report(telegram_id: int, task_id: int, photo_id: str, amount: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as c:
            row = await c.fetchone()
        if not row:
            return 0
        user_id = row["id"]
        cursor = await db.execute("""
            INSERT INTO reports (user_id, task_id, photo_file_id, amount)
            VALUES (?, ?, ?, ?)
        """, (user_id, task_id, photo_id, amount))
        await db.commit()
        return cursor.lastrowid


async def get_report(report_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT r.*, u.telegram_id, u.nickname, t.title, t.task_type
            FROM reports r
            JOIN users u ON u.id = r.user_id
            JOIN tasks t ON t.id = r.task_id
            WHERE r.id = ?
        """, (report_id,)) as c:
            row = await c.fetchone()
            return dict(row) if row else None


async def accept_report(report_id: int):
    """Принять отчёт: обновить прогресс, репутацию, склад."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT r.*, u.telegram_id, t.task_type, t.required_amount
            FROM reports r
            JOIN users u ON u.id = r.user_id
            JOIN tasks t ON t.id = r.task_id
            WHERE r.id = ?
        """, (report_id,)) as c:
            report = await c.fetchone()
        if not report:
            return
        report = dict(report)

        # Обновить статус отчёта
        await db.execute(
            "UPDATE reports SET status = 'accepted' WHERE id = ?", (report_id,)
        )

        # Обновить прогресс user_task
        await db.execute("""
            UPDATE user_tasks
            SET progress = MIN(progress + ?, (SELECT required_amount FROM tasks WHERE id = ?))
            WHERE user_id = ? AND task_id = ?
        """, (report["amount"], report["task_id"], report["user_id"], report["task_id"]))

        # Проверить, выполнена ли задача
        async with db.execute("""
            SELECT ut.progress, t.required_amount FROM user_tasks ut
            JOIN tasks t ON t.id = ut.task_id
            WHERE ut.user_id = ? AND ut.task_id = ?
        """, (report["user_id"], report["task_id"])) as c:
            ut = await c.fetchone()
        if ut and ut[0] >= ut[1]:
            await db.execute("""
                UPDATE user_tasks SET status = 'done'
                WHERE user_id = ? AND task_id = ?
            """, (report["user_id"], report["task_id"]))

        await db.commit()

    # Начислить репутацию (+5 за отчёт)
    await add_reputation(report["telegram_id"], 5)

    # Пополнить склад
    await add_to_warehouse(report["task_type"], report["amount"])


async def reject_report(report_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE reports SET status = 'rejected' WHERE id = ?", (report_id,)
        )
        await db.commit()


async def get_tasks_with_deadline() -> list:
    """Для планировщика — задачи с дедлайном сегодня/завтра."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT t.*, ut.user_id, u.telegram_id, ut.progress
            FROM tasks t
            JOIN user_tasks ut ON ut.task_id = t.id
            JOIN users u ON u.id = ut.user_id
            WHERE t.status = 'active'
              AND ut.status = 'active'
              AND date(t.deadline) <= date('now', '+1 day')
        """) as c:
            return [dict(r) for r in await c.fetchall()]
