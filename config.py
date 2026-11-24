"""Настройки бота.

Токен бота берётся из переменной окружения BOT_TOKEN.
Можно задать его в файле .env или в переменных окружения системы.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Путь к папке проекта.
BASE_DIR = Path(__file__).resolve().parent

# Загружаем переменные из .env (если файл есть).
load_dotenv(BASE_DIR / ".env")

# Токен Telegram-бота. Задайте его в переменной окружения BOT_TOKEN
# или в файле .env: BOT_TOKEN=123456:ABC...
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Необязательный прокси для доступа к Telegram API, например
# socks5://127.0.0.1:10808 или http://127.0.0.1:10808.
# Если переменная не задана, бот работает без прокси.
PROXY_URL = os.getenv("PROXY_URL", "")

# Путь к файлу базы данных SQLite.
# База будет создана рядом с main.py в папке проекта.
DB_PATH = BASE_DIR / "tasks.db"
