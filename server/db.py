# server/db.py
import sqlite3
import json
from typing import List, Optional
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


# ---------- BOTS ----------

def save_bot(bot: dict):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO bots (bot_id, data) VALUES (?, ?)",
            (bot["bot_id"], json.dumps(bot))
        )
        conn.commit()


def delete_bot(bot_id: str):
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM bots WHERE bot_id = ?", (bot_id,))
            conn.commit()
    except Exception as e:
        print(f"[!] Failed to delete bot {bot_id} from DB: {e}")


def load_all_bots() -> List[dict]:
    """Список ботов для state.load_from_db()."""
    out = []
    with get_conn() as conn:
        cursor = conn.execute("SELECT bot_id, data FROM bots")
        for row in cursor:
            out.append(json.loads(row["data"]))
    return out


def max_meepo_num() -> int:
    m = 0
    for b in load_all_bots():
        n = b.get("meepo_num") or 0
        if n > m:
            m = n
    return m


# ---------- TASKS ----------

def save_task(task: dict):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO tasks (task_id, data) VALUES (?, ?)",
            (task["task_id"], json.dumps(task))
        )
        conn.commit()


def load_all_tasks() -> List[dict]:
    """Список задач для state.load_from_db()."""
    out = []
    with get_conn() as conn:
        cursor = conn.execute("SELECT task_id, data FROM tasks")
        for row in cursor:
            out.append(json.loads(row["data"]))
    return out


def get_task(task_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT data FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
    return json.loads(row["data"]) if row else None