# server/logic.py
import time
from config import BOT_TIMEOUT
from state import BOTS, TASKS, broadcast, bots_snapshot, tasks_snapshot
import db

# (Здесь остаются твои функции create_simple_task, create_composite_task, recompute_parents и т.д. 
# Я показываю только ту часть, которую нужно исправить или добавить)

def cleanup():
    """Удаляет мертвых ботов и возвращает их задачи в очередь."""
    now = time.time()
    dead_bots = []
    
    # Ищем ботов, которые не слали heartbeat
    for bot_id, bot in list(BOTS.items()):
        if now - bot.get("last_seen", 0) > BOT_TIMEOUT:
            dead_bots.append(bot_id)
            
    for bot_id in dead_bots:
        print(f"[!] Bot {bot_id} timed out. Removing.")
        
        # Возвращаем задачу, если агент упал во время её выполнения
        cur = BOTS[bot_id].get("current_task")
        if cur and cur in TASKS and TASKS[cur]["status"] == "running":
            TASKS[cur]["status"] = "pending"
            TASKS[cur]["bot_id"] = None
            TASKS[cur]["started_at"] = None
            db.save_task(TASKS[cur])
        
        # Удаляем из оперативной памяти и из БД
        del BOTS[bot_id]
        db.delete_bot(bot_id)
        
    if dead_bots:
        # Если кого-то удалили, нужно обновить панель
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcast({"type": "bots", "bots": bots_snapshot()}))
            loop.create_task(broadcast({"type": "tasks", "tasks": tasks_snapshot()}))
        except RuntimeError:
            pass # Если мы не в асинхронном контексте, пропускаем