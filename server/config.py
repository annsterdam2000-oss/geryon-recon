# server/config.py
# ☄ Zeus' thunder — timeouts, retries, the laws of the server.
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Таймауты (в секундах)
BOT_TIMEOUT = 30
BOT_REMOVE_AFTER = 120
TASK_TIMEOUT = 300
SUBTASK_TIMEOUT = 60
TASK_MAX_RETRIES = 3

# Простые модули — задача выполняется одним агентом целиком
SIMPLE_MODULES = [
    "email",
    "email_reg",
    "domain",
    "ip",
    "phone",
    "person",
    "telegram",
    "geo",
    "exif",
]

# Путь к БД
DB_PATH = Path(__file__).resolve().parent / "osint.db"

# --- хост и порт сервера ---
# 127.0.0.1 — только локально (безопасно везде)
# 0.0.0.0   — доступен в локальной сети (дома, для панели с телефона)
HOST = "0.0.0.0"
PORT = 5555

# --- Секретный ключ для API ---
# Если переменной окружения нет, используется дефолтный ключ (поменяй его на свой!)
API_TOKEN = os.getenv("GERYON_API_TOKEN", "geryon_secret_key_2026")