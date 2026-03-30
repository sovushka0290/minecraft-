from aiogram import Bot
from services.task_service import get_tasks_with_deadline
from services.task_service import progress_bar


async def check_deadlines(bot: Bot):
    tasks = await get_tasks_with_deadline()
    for t in tasks:
        bar = progress_bar(t["progress"], t["required_amount"])
        text = (
            f"⏰ <b>Напоминание о задаче</b>\n\n"
            f"📋 <b>{t['title']}</b>\n"
            f"📦 Тип: {t['task_type']}\n"
            f"📊 Прогресс: {bar}\n"
            f"🗓 Дедлайн: {t['deadline']}\n\n"
            f"Не забудь сдать отчёт!"
        )
        try:
            await bot.send_message(t["telegram_id"], text, parse_mode="HTML")
        except Exception:
            pass
