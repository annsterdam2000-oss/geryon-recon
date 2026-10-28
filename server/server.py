# server/server.py
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import HOST, PORT

from state import BOTS, TASKS
import db
from routes import agent, panel

app = FastAPI()

# Подключаем роутеры
app.include_router(agent.router)
app.include_router(panel.router)

# Отдаем статику (панель)
app.mount("/static", StaticFiles(directory="panel"), name="static")


@app.on_event("startup")
async def startup_event():
    print("[*] Geryon Recon — starting up...")
    
    # Инициализация БД (создание таблиц, если их нет)
    db.init_db()
    
    # Загружаем ботов и задачи из БД в память
    loaded_bots = db.load_bots()
    loaded_tasks = db.load_tasks()
    
    BOTS.update(loaded_bots)
    TASKS.update(loaded_tasks)
    
    print(f"[+] loaded {len(BOTS)} bots, {len(TASKS)} tasks from DB")

    # --- ВОССТАНОВЛЕНИЕ ОЧЕРЕДИ ---
    # Если задача была в статусе 'running', но сервер перезапустился,
    # возвращаем её в очередь (pending), чтобы агенты могли её взять.
    restored_count = 0
    for tid, t in TASKS.items():
        if t.get("status") == "running":
            t["status"] = "pending"
            t["bot_id"] = None
            t["started_at"] = None
            db.save_task(t)
            restored_count += 1
            
    if restored_count > 0:
        print(f"[*] Restored {restored_count} running tasks to pending queue")

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)