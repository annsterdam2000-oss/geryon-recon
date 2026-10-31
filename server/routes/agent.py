# server/routes/agent.py
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends

from models import RegisterReq, HeartbeatReq, ResultReq
from state import (BOTS, TASKS, broadcast, bots_snapshot, tasks_snapshot,
                   next_meepo_num)
from logic import recompute_parents
from notify import notify_task_done
from deps import verify_token
import db


router = APIRouter()


@router.post("/register", dependencies=[Depends(verify_token)])
async def register(req: RegisterReq):
    bot_id = str(uuid.uuid4())[:8]
    meepo_num = next_meepo_num()
    agent_name = f"Meepo {meepo_num}"

    info = {"os": req.os, "user": req.user}
    if req.hardware is not None:
        info["hardware"] = req.hardware

    bot = {
        "agent_name": agent_name,
        "meepo_num": meepo_num,
        "hostname": req.hostname,
        "info": info,
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


@router.post("/heartbeat/{bot_id}", dependencies=[Depends(verify_token)])
async def heartbeat(bot_id: str, req: Optional[HeartbeatReq] = None):
    if bot_id not in BOTS:
        return {"ok": False, "error": "unknown bot"}

    BOTS[bot_id]["last_seen"] = time.time()

    if req is not None and req.hardware is not None:
        BOTS[bot_id].setdefault("info", {})
        BOTS[bot_id]["info"]["hardware"] = req.hardware

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


@router.post("/result", dependencies=[Depends(verify_token)])
async def result(req: ResultReq):
    if req.task_id in TASKS:
        t = TASKS[req.task_id]

        # --- ЗАЩИТА ОТ ДУБЛИРОВАНИЯ ---
        # Если задача уже выполнена или провалена, не принимаем результат повторно
        if t.get("status") in ("done", "failed"):
            print(f"[!] Duplicate result ignored for task {req.task_id} (status: {t.get('status')})")
            return {"ok": False, "error": "task already completed"}

        # Проверка, что задачу выполняет именно этот бот
        if t.get("bot_id") != req.bot_id:
            return {"ok": False, "error": "task assigned to another bot"}

        t["status"] = req.status
        t["result"] = req.result
        t["error"] = req.error
        t["finished_at"] = time.time()
        db.save_task(t)

        # Пересчитываем статус родителя (если это подзадача)
        recompute_parents()

        # Уведомление в Discord о завершённой задаче
        notify_task_done(t)

    if req.bot_id in BOTS:
        BOTS[req.bot_id]["current_task"] = None
    print(f"[=] result {req.task_id} from {req.bot_id}: {req.status}")

    # Синхронизируем клиентов панели
    await broadcast({"type": "bots", "bots": bots_snapshot()})
    await broadcast({"type": "tasks", "tasks": tasks_snapshot()})

    return {"ok": True}