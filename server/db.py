# server/db.py
import sqlite3
import json
from config import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                bot_id TEXT PRIMARY KEY,
                data TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                data TEXT
            )
        """)
        conn.commit()

def save_bot(bot: dict):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO bots (bot_id, data) VALUES (?, ?)",
            (bot["bot_id"], json.dumps(bot))
        )
        conn.commit()

def load_bots() -> dict:
    bots = {}
    with get_conn() as conn:
        cursor = conn.execute("SELECT bot_id, data FROM bots")
        for row in cursor:
            bots[row["bot_id"]] = json.loads(row["data"])
    return bots

# --- НОВАЯ ФУНКЦИЯ ---
def delete_bot(bot_id: str):
    """Удаляет бота из базы данных по его ID."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM bots WHERE bot_id = ?", (bot_id,))
            conn.commit()
    except Exception as e:
        print(f"[!] Failed to delete bot {bot_id} from DB: {e}")

def save_task(task: dict):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO tasks (task_id, data) VALUES (?, ?)",
            (task["task_id"], json.dumps(task))
        )
        conn.commit()

def load_tasks() -> dict:
    tasks = {}
    with get_conn() as conn:
        cursor = conn.execute("SELECT task_id, data FROM tasks")
        for row in cursor:
            tasks[row["task_id"]] = json.loads(row["data"])
    return tasks