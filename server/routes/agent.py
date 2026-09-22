# server/routes/agent.py
import time
import uuid

from fastapi import APIRouter

from models import RegisterReq, ResultReq
from state import (BOTS, TASKS, broadcast, bots_snapshot, tasks_snapshot,
                   next_meepo_num)
from logic import recompute_parents
from notify import notify_task_done
import db


router = APIRouter()


@router.post("/register")
async def register(req: RegisterReq):
    bot_id = str(uuid.uuid4())[:8]
    meepo_num = next_meepo_num()
    agent_name = f"Meepo {meepo_num}"

    bot = {
        "agent_name": agent_name,
        "meepo_num": meepo_num,
        "hostname": req.hostname,
        "info": {"os": req.os, "user": req.user},
        "modules": req.modules or ["email"],
        "last_seen": time.time(),
        "current_task": None,
        "first_seen": time.time(),
    }
    BOTS[bot_id] = bot
    bot["bot_id"] = bot_id
    db.save_bot(bot)

    print(f"[+] {agent_name} registered (id: {bot_id}) modules={req.modules}")
    await broadcast({"type": "bots", "bots": bots_snapshot()})
    return {"bot_id": bot_id, "agent_name": agent_name, "meepo_num": meepo_num}


@router.post("/heartbeat/{bot_id}")
async def heartbeat(bot_id: str):
    if bot_id not in BOTS:
        return {"ok": False, "error": "unknown bot"}
    BOTS[bot_id]["last_seen"] = time.time()

    task = None
    if BOTS[bot_id]["current_task"] is None:
        task = _find_task_for_bot(bot_id)

    await broadcast({"type": "bots", "bots": bots_snapshot()})
    await broadcast({"type": "tasks", "tasks": tasks_snapshot()})
    return {"ok": True, "task": task}


def _find_task_for_bot(bot_id: str):
    bot_modules = BOTS[bot_id]["modules"]

    if "http_check" in bot_modules:
        for tid, t in TASKS.items():
            if t["status"] != "pending":
                continue
            if not t.get("parent_id"):
                continue
            t["status"] = "running"
            t["bot_id"] = bot_id
            t["started_at"] = time.time()
            BOTS[bot_id]["current_task"] = tid
            db.save_task(t)
            return {
                "task_id": tid,
                "task_type": "http_check",
                "site": t["site"],
                "url": t["url"],
                "found_codes": t["found_codes"],
                "not_found_codes": t["not_found_codes"],
            }

    for tid, t in TASKS.items():
        if t["status"] != "pending":
            continue
        if t.get("parent_id"):
            continue
        if t["task_type"] not in bot_modules:
            continue
        t["status"] = "running"
        t["bot_id"] = bot_id
        t["started_at"] = time.time()
        BOTS[bot_id]["current_task"] = tid
        db.save_task(t)
        return {"task_id": tid, "task_type": t["task_type"], "target": t["target"]}

    return None


@router.post("/result")
async def result(req: ResultReq):
    if req.task_id in TASKS:
        t = TASKS[req.task_id]
        if t.get("bot_id") != req.bot_id:
            return {"ok": False, "error": "task assigned to another bot"}
        t["status"] = req.status
        t["result"] = req.result
        t["error"] = req.error
        t["finished_at"] = time.time()
        db.save_task(t)
    if req.bot_id in BOTS:
        BOTS[req.bot_id]["current_task"] = None
    print(f"[=] result {req.task_id} from {req.bot_id}: {req.status}")

    was_parent_done = False
    if req.task_id in TASKS:
        t = TASKS[req.task_id]
        if t.get("parent_id"):
            parent = TASKS.get(t["parent_id"])
            if parent and parent.get("status") == "done":
                was_parent_done = True

    recompute_parents(time.time())

    notify_target = None
    if req.task_id in TASKS:
        t = TASKS[req.task_id]
        if t.get("parent_id"):
            parent = TASKS.get(t["parent_id"])
            if parent and parent.get("status") == "done" and not was_parent_done:
                notify_target = parent
        else:
            if t.get("status") in ("done", "failed"):
                notify_target = t

    if notify_target:
        try:
            notify_task_done(notify_target)
        except Exception as e:
            print(f"[!] notify failed: {e}")

    await broadcast({"type": "tasks", "tasks": tasks_snapshot()})
    await broadcast({"type": "bots", "bots": bots_snapshot()})
    return {"ok": True}