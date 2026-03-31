import os
from dotenv import load_dotenv

load_dotenv()

# Обязательные переменные
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Необязательные (с дефолтными значениями)
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
PORT = int(os.getenv("PORT", 10000))

# Проверка на ошибки при старте
if not BOT_TOKEN:
    print("❌ ОШИБКА: Переменная BOT_TOKEN не установлена!")
if not DATABASE_URL:
    print("❌ ОШИБКА: Переменная DATABASE_URL не установлена!")
