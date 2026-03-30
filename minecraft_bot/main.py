import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from database.models import init_db
from handlers import user, admin
from services.scheduler_service import check_deadlines

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Заглушка для Render (фиктивный веб-сервер) ---
async def health_check(request):
    return web.Response(text="Minecraft State Bot is alive and working!")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render передает порт через переменную окружения PORT
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Dummy web server started on port {port} for Render")
# --------------------------------------------------


async def main():
    await init_db()

    # Запускаем наш веб-сервер перед ботом
    await start_web_server()

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(user.router)
    dp.include_router(admin.router)

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(check_deadlines, "interval", hours=1, args=[bot])
    scheduler.start()

    logger.info("Бот запущен")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
