import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла (для локалки)
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID администратора
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Тот самый URL базы данных, который мы забыли
DATABASE_URL = os.getenv("DATABASE_URL")

# Путь к SQLite (оставь на всякий случай, если где-то еще используется)
DB_PATH = "database.db"
