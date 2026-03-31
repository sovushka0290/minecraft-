import os
from dotenv import load_dotenv

# Загружаем .env для локальной разработки
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID администратора (по умолчанию 0)
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# ТА САМАЯ ПЕРЕМЕННАЯ (её не хватало)
DATABASE_URL = os.getenv("DATABASE_URL")

# Путь к SQLite (если еще где-то нужен)
DB_PATH = "database.db"
