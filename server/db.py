# server/db.py
"""
Работа с SQLite. Простая синхронная обёртка.
"""
import json
import sqlite3
import time
from pathlib import Path
from typing import Optional, List, Dict

from config import DB_PATH


_conn: Optional[sqlite3.Connection] = None


def init_db():
    """Создаёт таблицы, если их нет."""
    global _conn
    _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    _conn.row_factory = sqlite3.Row

    _conn.executescript("""
    CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        parent_id TEXT,
        task_type TEXT NOT NULL,
        target TEXT,
        site TEXT,
        url TEXT,
        status TEXT NOT NULL,
        bot_id TEXT,
        result TEXT,
        error TEXT,
        created_at REAL,
        started_at REAL,
        finished_at REAL,
        retries INTEGER DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_id);
    CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
    CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type);
    CREATE INDEX IF NOT EXISTS idx_tasks_target ON tasks(target);

    CREATE TABLE IF NOT EXISTS bots (
        bot_id TEXT PRIMARY KEY,
        agent_name TEXT,
        meepo_num INTEGER,
        hostname TEXT,
        os TEXT,
        user TEXT,
        modules TEXT,
        first_seen REAL,
        last_seen REAL
    );
    """)

    # Миграция: если таблица bots уже была без новых колонок — добавим
    _migrate_bots_columns()

    _conn.commit()
    print(f"[+] DB initialized: {DB_PATH}")


def _migrate_bots_columns():
    """Добавляет agent_name и meepo_num, если их нет (для существующих баз)."""
    if _conn is None:
        return
    try:
        cols = {r["name"] for r in _conn.execute("PRAGMA table_info(bots)").fetchall()}
        if "agent_name" not in cols:
            _conn.execute("ALTER TABLE bots ADD COLUMN agent_name TEXT")
            print("[+] migration: added bots.agent_name")
        if "meepo_num" not in cols:
            _conn.execute("ALTER TABLE bots ADD COLUMN meepo_num INTEGER")
            print("[+] migration: added bots.meepo_num")
    except Exception as e:
        print(f"[!] migration error: {e}")


def save_task(t: dict):
    """UPSERT задачи."""
    if _conn is None:
        return
    try:
        _conn.execute("""
            INSERT INTO tasks (task_id, parent_id, task_type, target, site, url,
                               status, bot_id, result, error, created_at,
                               started_at, finished_at, retries)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                status=excluded.status,
                bot_id=excluded.bot_id,
                result=excluded.result,
                error=excluded.error,
                started_at=excluded.started_at,
                finished_at=excluded.finished_at,
                retries=excluded.retries
        """, (
            t["task_id"],
            t.get("parent_id"),
            t.get("task_type"),
            t.get("target"),
            t.get("site"),
            t.get("url"),
            t.get("status"),
            t.get("bot_id"),
            json.dumps(t.get("result", {}), ensure_ascii=False),
            t.get("error", ""),
            t.get("created_at"),
            t.get("started_at"),
            t.get("finished_at"),
            t.get("retries", 0),
        ))
        _conn.commit()
    except Exception as e:
        print(f"[!] save_task error: {e}")


def save_bot(b: dict):
    if _conn is None:
        return
    try:
        _conn.execute("""
            INSERT INTO bots (bot_id, agent_name, meepo_num, hostname, os, user,
                              modules, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(bot_id) DO UPDATE SET
                agent_name=excluded.agent_name,
                meepo_num=excluded.meepo_num,
                hostname=excluded.hostname,
                os=excluded.os,
                user=excluded.user,
                modules=excluded.modules,
                last_seen=excluded.last_seen
        """, (
            b["bot_id"],
            b.get("agent_name"),
            b.get("meepo_num"),
            b.get("hostname"),
            b.get("info", {}).get("os"),
            b.get("info", {}).get("user"),
            json.dumps(b.get("modules", []), ensure_ascii=False),
            b.get("first_seen", time.time()),
            b.get("last_seen", time.time()),
        ))
        _conn.commit()
    except Exception as e:
        print(f"[!] save_bot error: {e}")


def max_meepo_num() -> int:
    """Максимальный номер Meepo в базе (0, если пусто)."""
    if _conn is None:
        return 0
    try:
        row = _conn.execute("SELECT COALESCE(MAX(meepo_num), 0) AS m FROM bots").fetchone()
        return int(row["m"] or 0)
    except Exception as e:
        print(f"[!] max_meepo_num error: {e}")
        return 0


def load_all_tasks() -> List[dict]:
    """Загружает все задачи при старте сервера."""
    if _conn is None:
        return []
    try:
        rows = _conn.execute("SELECT * FROM tasks").fetchall()
        out = []
        for r in rows:
            out.append({
                "task_id": r["task_id"],
                "parent_id": r["parent_id"],
                "task_type": r["task_type"],
                "target": r["target"],
                "site": r["site"],
                "url": r["url"],
                "status": r["status"],
                "bot_id": r["bot_id"],
                "result": json.loads(r["result"]) if r["result"] else {},
                "error": r["error"] or "",
                "created_at": r["created_at"],
                "started_at": r["started_at"],
                "finished_at": r["finished_at"],
                "retries": r["retries"] or 0,
            })
        return out
    except Exception as e:
        print(f"[!] load_all_tasks error: {e}")
        return []


def load_all_bots() -> List[dict]:
    if _conn is None:
        return []
    try:
        rows = _conn.execute("SELECT * FROM bots").fetchall()
        out = []
        for r in rows:
            out.append({
                "bot_id": r["bot_id"],
                "agent_name": r["agent_name"],
                "meepo_num": r["meepo_num"],
                "hostname": r["hostname"],
                "info": {"os": r["os"], "user": r["user"]},
                "modules": json.loads(r["modules"]) if r["modules"] else [],
                "first_seen": r["first_seen"],
                "last_seen": r["last_seen"],
            })
        return out
    except Exception as e:
        print(f"[!] load_all_bots error: {e}")
        return []


def close():
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None