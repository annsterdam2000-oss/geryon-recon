# server/state.py
import time
from typing import Dict, List
from fastapi import WebSocket

from config import BOT_TIMEOUT
import db


BOTS: Dict[str, dict] = {}
TASKS: Dict[str, dict] = {}


def bot_status(bot: dict) -> str:
    return "online" if time.time() - bot["last_seen"] < BOT_TIMEOUT else "offline"


def is_parent(task: dict) -> bool:
    return "subtasks" in task


def next_meepo_num() -> int:
    """Следующий номер Meepo. Учитывает и живых ботов в BOTS, и историю в БД."""
    in_memory = [b.get("meepo_num", 0) for b in BOTS.values()]
    in_db = db.max_meepo_num()
    current_max = max(in_memory + [in_db, 0])
    return current_max + 1


def bots_snapshot() -> List[dict]:
    return [
        {
            "bot_id": bid,
            "agent_name": b.get("agent_name", bid),
            "meepo_num": b.get("meepo_num"),
            "hostname": b["hostname"],
            "info": b["info"],
            "modules": b["modules"],
            "status": bot_status(b),
            "current_task": b.get("current_task"),
            "last_seen": b["last_seen"],
        }
        for bid, b in BOTS.items()
    ]


def tasks_snapshot() -> List[dict]:
    out = []
    for tid, t in TASKS.items():
        if t.get("parent_id"):
            continue
        item = dict(t)
        if is_parent(t):
            item["subtasks_full"] = [
                TASKS[sid] for sid in t["subtasks"] if sid in TASKS
            ]
        out.append(item)
    return out


def load_from_db():
    """Загружает BOTS и TASKS из БД при старте сервера."""
    global BOTS, TASKS

    # Загружаем ботов
    for b in db.load_all_bots():
        BOTS[b["bot_id"]] = {
            "agent_name": b.get("agent_name") or b["bot_id"],
            "meepo_num": b.get("meepo_num"),
            "hostname": b["hostname"],
            "info": b["info"],
            "modules": b["modules"],
            "last_seen": b["last_seen"],
            "current_task": None,
            "first_seen": b.get("first_seen"),
        }

    # Загружаем задачи
    loaded_tasks = db.load_all_tasks()
    for t in loaded_tasks:
        TASKS[t["task_id"]] = t

    # Восстанавливаем связь родитель ↔ подзадачи
    for tid, t in TASKS.items():
        pid = t.get("parent_id")
        if pid and pid in TASKS:
            parent = TASKS[pid]
            if "subtasks" not in parent:
                parent["subtasks"] = []
            if tid not in parent["subtasks"]:
                parent["subtasks"].append(tid)

    # Сбрасываем статус "running" у задач — они были прерваны
    for tid, t in TASKS.items():
        if t.get("status") == "running":
            t["status"] = "pending"
            t["bot_id"] = None
            t["started_at"] = None
            db.save_task(t)

    print(f"[+] loaded {len(BOTS)} bots, {len(TASKS)} tasks from DB")


class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, msg: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


async def broadcast(msg: dict):
    await manager.broadcast(msg)