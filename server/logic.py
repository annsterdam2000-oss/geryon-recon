# server/logic.py
import time
import uuid
import asyncio
from typing import Optional

from config import BOT_TIMEOUT, TASK_TIMEOUT, SUBTASK_TIMEOUT, TASK_MAX_RETRIES
from state import BOTS, TASKS, broadcast, bots_snapshot, tasks_snapshot
from sites import COMPOSITE_MODULES
import db


def _new_task(
    task_type: str,
    target: str,
    parent_id: Optional[str] = None,
    **extra,
) -> dict:
    now = time.time()
    timeout = SUBTASK_TIMEOUT if parent_id else TASK_TIMEOUT
    task = {
        "task_id": str(uuid.uuid4()),
        "task_type": task_type,
        "target": target,
        "status": "pending",
        "bot_id": None,
        "parent_id": parent_id,
        "created_at": now,
        "started_at": None,
        "finished_at": None,
        "deadline_at": now + timeout,
        "retries": 0,
        "max_retries": TASK_MAX_RETRIES,
        "result": None,
        "error": None,
    }
    task.update(extra)
    return task


def create_simple_task(task_type: str, target: str) -> str:
    """Один модуль — одна задача."""
    task = _new_task(task_type, target)
    TASKS[task["task_id"]] = task
    db.save_task(task)
    return task["task_id"]


def create_composite_task(task_type: str, target: str) -> str:
    """
    Составная задача: родитель + подзадачи.
    Сейчас поддержан только 'username' → 35 подзадач http_check.
    """
    sites = COMPOSITE_MODULES.get(task_type)
    if sites is None:
        raise ValueError(f"unknown composite task type: {task_type}")

    parent = _new_task(task_type, target)
    parent["subtasks"] = []
    TASKS[parent["task_id"]] = parent
    db.save_task(parent)

    for site, url_tpl, found, notfound in sites:
        sub = _new_task(
            "http_check",
            target,
            parent_id=parent["task_id"],
            site=site,
            url=url_tpl.format(u=target),
            found_codes=found,
            not_found_codes=notfound,
        )
        TASKS[sub["task_id"]] = sub
        parent["subtasks"].append(sub["task_id"])
        db.save_task(sub)

    db.save_task(parent)  # ещё раз, уже с заполненным subtasks
    return parent["task_id"]


def recompute_parents():
    """
    Пересчитывает статус родителя и собирает красивые результаты для панели.
    """
    for tid, t in TASKS.items():
        if "subtasks" not in t:
            continue
        
        subs = [TASKS[sid] for sid in t["subtasks"] if sid in TASKS]
        if not subs:
            continue
        
        statuses = {s.get("status") for s in subs}
        
        # 1. Определяем статус родителя
        if "running" in statuses:
            new_status = "running"
        elif statuses <= {"done", "failed"}:
            new_status = "done"  # Даже если часть упала, задача завершена
        else:
            new_status = "pending"
            
        # 2. Если задача только что завершилась, собираем результаты
        if new_status == "done" and t.get("status") != "done":
            found_count = 0
            results_list = []
            
            # Проходимся по каждой выполненной подзадаче
            for s in subs:
                site_name = s.get("site", "?")
                sub_status = s.get("status", "?")
                
                # Проверяем, нашли ли мы ник на сайте. 
                # (Агент должен присылать в result флаг "found", либо мы считаем "done" успехом)
                is_found = False
                if sub_status == "done":
                    # Если агент присылает result с полем found, используем его.
                    # Если нет — считаем, что раз статус done, то ник найден.
                    res = s.get("result", {})
                    if isinstance(res, dict) and "found" in res:
                        is_found = res["found"]
                    else:
                        is_found = True 
                        
                if is_found:
                    found_count += 1
                    
                results_list.append({
                    "site": site_name,
                    "status": "found" if is_found else "not_found",
                    "error": s.get("error") if sub_status == "failed" else None
                })
            
            # Складываем всё в родителя. 
            # Структура полностью совпадает с тем, что ждет твой panel.js
            t["result"] = {
                "found_count": found_count,
                "total": len(subs),
                "results": results_list
            }
            
        # 3. Сохраняем в БД, если статус изменился или мы только что собрали результат
        if t.get("status") != new_status or new_status == "done":
            t["status"] = new_status
            db.save_task(t)


def cleanup():
    """Удаляет мертвых ботов и возвращает их задачи в очередь."""
    now = time.time()
    dead_bots = [
        bid for bid, b in BOTS.items()
        if now - b.get("last_seen", 0) > BOT_TIMEOUT
    ]
    if not dead_bots:
        return

    for bot_id in dead_bots:
        print(f"[!] Bot {bot_id} timed out. Removing.")
        cur = BOTS[bot_id].get("current_task")
        if cur and cur in TASKS and TASKS[cur]["status"] == "running":
            TASKS[cur]["status"] = "pending"
            TASKS[cur]["bot_id"] = None
            TASKS[cur]["started_at"] = None
            db.save_task(TASKS[cur])
        del BOTS[bot_id]
        db.delete_bot(bot_id)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(broadcast({
        "type": "state",
        "bots": bots_snapshot(),
        "tasks": tasks_snapshot(),
    }))