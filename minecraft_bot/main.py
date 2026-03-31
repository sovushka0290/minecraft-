import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Импорты твоих модулей
from config import BOT_TOKEN
from database.models import init_db
from handlers import user, admin
from services.scheduler_service import check_deadlines

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Секция для Render (Web Service Support) ---
async def handle_health_check(request):
    """Ответ для Render, что сервис жив."""
    return web.Response(text="Minecraft State Bot is running!", status=200)

async def run_dummy_server():
    """Запуск легкого веб-сервера на фоне."""
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render автоматически подставляет PORT, если нет — используем 10000
    port = int(os.getenv("PORT", 10000)) 
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    logger.info(f"🌐 Фиктивный сервер запущен на порту {port} (для Render)")
    await site.start()

# --- Основная логика бота ---
async def main():
    logger.info("🚀 Запуск инициализации...")

    # 1. Инициализация базы данных (PostgreSQL)
    try:
        await init_db()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при инициализации БД: {e}")
        # Не останавливаем, если хотим проверить логи, но БД важна
    
    # 2. Запуск веб-сервера для прохождения Port Check на Render
    await run_dummy_server()

    # 3. Настройка бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем роутеры
    dp.include_router(admin.router) # Админские команды обычно приоритетнее
    dp.include_router(user.router)

    # 4. Настройка планировщика (APScheduler)
    scheduler = AsyncIOScheduler(timezone="UTC")
    # Проверка дедлайнов каждый час
    scheduler.add_job(check_deadlines, "interval", hours=1, args=[bot])
    scheduler.start()
    logger.info("⏰ Планировщик задач запущен")

    # 5. Запуск Polling
    logger.info("🤖 Бот вышел в онлайн!")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
