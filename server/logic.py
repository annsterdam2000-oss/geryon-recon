# server/logic.py
import time
import uuid

from config import (
    BOT_TIMEOUT, BOT_REMOVE_AFTER,
    TASK_TIMEOUT, SUBTASK_TIMEOUT, TASK_MAX_RETRIES,
)
from sites import COMPOSITE_MODULES
from state import BOTS, TASKS, is_parent
import db


def _save(t: dict):
    """Обёртка — сохраняет задачу в БД."""
    db.save_task(t)


def cleanup():
    now = time.time()

    # 1. Простые задачи, чей бот оффлайн
    for tid, t in TASKS.items():
        if t["status"] != "running":
            continue
        if is_parent(t):
            continue
        if t.get("parent_id"):
            continue
        bot_id = t.get("bot_id")
        bot = BOTS.get(bot_id)
        bot_offline = (bot is None) or (now - bot["last_seen"] > BOT_TIMEOUT)
        task_timed_out = (t.get("started_at") is not None
                          and now - t["started_at"] > TASK_TIMEOUT)

        if not (bot_offline or task_timed_out):
            continue

        if bot is not None and bot.get("current_task") == tid:
            bot["current_task"] = None

        t["retries"] = t.get("retries", 0) + 1
        if t["retries"] > TASK_MAX_RETRIES:
            t["status"] = "failed"
            t["error"] = ("bot offline during execution"
                          if bot_offline else "task timeout")
            t["finished_at"] = now
        else:
            t["status"] = "pending"
            t["bot_id"] = None
            t["started_at"] = None
            t["error"] = ""
        _save(t)

    # 2. Зависшие подзадачи
    for tid, t in TASKS.items():
        if not t.get("parent_id"):
            continue
        if t["status"] != "pending":
            continue
        if now - (t.get("created_at") or now) > SUBTASK_TIMEOUT:
            t["status"] = "failed"
            t["error"] = "no agent available (timeout)"
            _save(t)

    # 3. Подзадачи, чей бот оффлайн
    for tid, t in TASKS.items():
        if not t.get("parent_id"):
            continue
        if t["status"] != "running":
            continue
        bot_id = t.get("bot_id")
        bot = BOTS.get(bot_id)
        bot_offline = (bot is None) or (now - bot["last_seen"] > BOT_TIMEOUT)
        if not bot_offline:
            continue
        if bot is not None and bot.get("current_task") == tid:
            bot["current_task"] = None
        t["retries"] = t.get("retries", 0) + 1
        if t["retries"] > TASK_MAX_RETRIES:
            t["status"] = "failed"
            t["error"] = "bot offline"
            t["finished_at"] = now
        else:
            t["status"] = "pending"
            t["bot_id"] = None
            t["started_at"] = None
            t["error"] = ""
        _save(t)

    # 4. Пересчёт родителей
    recompute_parents(now)

    # 5. Удаляем мёртвых ботов
    dead_bots = [b for b, d in BOTS.items() if now - d["last_seen"] > BOT_REMOVE_AFTER]
    for b in dead_bots:
        del BOTS[b]


def recompute_parents(now: float):
    for pid, p in list(TASKS.items()):
        if not is_parent(p):
            continue
        if p["status"] in ("done", "failed"):
            continue

        subtasks = [TASKS[sid] for sid in p["subtasks"] if sid in TASKS]
        done = sum(1 for s in subtasks if s["status"] == "done")
        failed = sum(1 for s in subtasks if s["status"] == "failed")
        running = sum(1 for s in subtasks if s["status"] == "running")
        pending = sum(1 for s in subtasks if s["status"] == "pending")
        total = len(subtasks)

        p["progress"] = f"{done + failed}/{total}"
        p["progress_done"] = done
        p["progress_failed"] = failed
        p["progress_running"] = running
        p["progress_pending"] = pending

        if pending == 0 and running == 0:
            p["status"] = "done"
            p["finished_at"] = now
            p["result"] = {
                "target": p["target"],
                "results": [
                    {
                        "site": s.get("site"),
                        "status": (s.get("result", {}).get("status")
                                   if s["status"] == "done" else "unknown"),
                        "http_code": s.get("result", {}).get("http_code"),
                        "url": s.get("result", {}).get("url"),
                        "error": s.get("error"),
                    }
                    for s in subtasks
                ],
                "found_count": sum(
                    1 for s in subtasks
                    if s["status"] == "done"
                    and s.get("result", {}).get("status") == "found"
                ),
                "unknown_count": sum(
                    1 for s in subtasks
                    if s["status"] != "done"
                    or s.get("result", {}).get("status") == "unknown"
                ),
                "total": total,
            }
        _save(p)


def create_composite_task(task_type: str, target: str):
    sites = COMPOSITE_MODULES[task_type]
    parent_id = str(uuid.uuid4())[:8]
    now = time.time()

    subtask_ids = []
    for site_name, url_tmpl, found_codes, not_found_codes in sites:
        stid = str(uuid.uuid4())[:8]
        url = url_tmpl.replace("{u}", target)
        st = {
            "task_id": stid,
            "parent_id": parent_id,
            "task_type": "http_check",
            "target": target,
            "site": site_name,
            "url": url,
            "found_codes": found_codes,
            "not_found_codes": not_found_codes,
            "bot_id": None,
            "status": "pending",
            "result": {},
            "error": "",
            "created_at": now,
            "started_at": None,
            "finished_at": None,
            "retries": 0,
        }
        TASKS[stid] = st
        _save(st)
        subtask_ids.append(stid)

    parent = {
        "task_id": parent_id,
        "task_type": task_type,
        "target": target,
        "status": "pending",
        "subtasks": subtask_ids,
        "progress": f"0/{len(sites)}",
        "progress_done": 0,
        "progress_failed": 0,
        "progress_running": 0,
        "progress_pending": len(sites),
        "created_at": now,
        "started_at": now,
        "finished_at": None,
    }
    TASKS[parent_id] = parent
    _save(parent)
    return parent_id


def create_simple_task(task_type: str, target: str):
    task_id = str(uuid.uuid4())[:8]
    t = {
        "task_id": task_id,
        "task_type": task_type,
        "target": target,
        "bot_id": None,
        "status": "pending",
        "result": {},
        "error": "",
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "retries": 0,
    }
    TASKS[task_id] = t
    _save(t)
    return task_id