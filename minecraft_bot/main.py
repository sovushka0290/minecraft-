import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, DATABASE_URL, PORT
from database.models import init_db
from handlers import user, admin

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
logger = logging.getLogger(__name__)

async def handle_ping(request):
    return web.Response(text="Bot is running")

async def start_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Web server started on port {PORT}")

async def main():
    logger.info("🚀 Старт приложения...")
    
    # 1. БД
    await init_db()
    
    # 2. Web server для Render
    await start_server()

    # 3. Bot
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(admin.router)
    dp.include_router(user.router)

    logger.info("🤖 Бот запускает polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"💥 КРИТИЧЕСКИЙ СБОЙ: {e}", exc_info=True)
        sys.exit(1)
