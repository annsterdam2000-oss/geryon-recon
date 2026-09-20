# server/routes/panel.py
from fastapi import APIRouter

from sites import COMPOSITE_MODULES
from models import TaskReq
from state import BOTS, TASKS, is_parent, broadcast, bots_snapshot, tasks_snapshot
from logic import cleanup, create_composite_task, create_simple_task
import db


router = APIRouter()


@router.post("/task")
async def create_task(req: TaskReq):
    if req.task_type in COMPOSITE_MODULES:
        task_id = create_composite_task(req.task_type, req.target)
        print(f"[+] composite task {task_id}: {req.task_type} -> {req.target}")
    else:
        task_id = create_simple_task(req.task_type, req.target)
        print(f"[+] task {task_id}: {req.task_type} -> {req.target}")
    await broadcast({"type": "tasks", "tasks": tasks_snapshot()})
    return {"ok": True, "task_id": task_id}


@router.get("/bots")
async def get_bots():
    cleanup()
    return bots_snapshot()


@router.get("/tasks")
async def get_tasks():
    cleanup()
    return tasks_snapshot()


@router.post("/remove/bot/{bot_id}")
async def remove_bot(bot_id: str):
    if bot_id not in BOTS:
        return {"ok": False, "error": "unknown bot"}
    cur = BOTS[bot_id].get("current_task")
    if cur and cur in TASKS and TASKS[cur]["status"] == "running":
        TASKS[cur]["status"] = "pending"
        TASKS[cur]["bot_id"] = None
        TASKS[cur]["started_at"] = None
        db.save_task(TASKS[cur])
    del BOTS[bot_id]
    await broadcast({"type": "bots", "bots": bots_snapshot()})
    await broadcast({"type": "tasks", "tasks": tasks_snapshot()})
    return {"ok": True}


@router.post("/remove/task/{task_id}")
async def remove_task(task_id: str):
    if task_id not in TASKS:
        return {"ok": False, "error": "unknown task"}
    t = TASKS[task_id]
    if is_parent(t):
        for sid in t["subtasks"]:
            if sid in TASKS:
                s = TASKS[sid]
                if s.get("bot_id") and s["bot_id"] in BOTS:
                    if BOTS[s["bot_id"]].get("current_task") == sid:
                        BOTS[s["bot_id"]]["current_task"] = None
                del TASKS[sid]
    if t.get("bot_id") and t["bot_id"] in BOTS:
        if BOTS[t["bot_id"]].get("current_task") == task_id:
            BOTS[t["bot_id"]]["current_task"] = None
    del TASKS[task_id]
    await broadcast({"type": "tasks", "tasks": tasks_snapshot()})
    await broadcast({"type": "bots", "bots": bots_snapshot()})
    return {"ok": True}