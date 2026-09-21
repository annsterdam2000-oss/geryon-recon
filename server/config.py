# server/config.py
from pathlib import Path

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