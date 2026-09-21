# server/config.py
from pathlib import Path

BOT_TIMEOUT = 30
BOT_REMOVE_AFTER = 120
TASK_TIMEOUT = 300
SUBTASK_TIMEOUT = 60
TASK_MAX_RETRIES = 3

SIMPLE_MODULES = ["email", "email_reg", "domain", "ip", "phone", "person", "telegram"]

DB_PATH = Path(__file__).resolve().parent / "osint.db"