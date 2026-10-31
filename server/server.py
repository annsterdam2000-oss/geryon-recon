# server/server.py
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from config import HOST, PORT

import db
from state import BOTS, TASKS, load_from_db
from routes import agent, panel

app = FastAPI()

# Подключаем роутеры
app.include_router(agent.router)
app.include_router(panel.router)

BASE_DIR = Path(__file__).resolve().parent.parent
PANEL_DIR = BASE_DIR / "panel"

# Оставляем статику для CSS, JS и картинок
app.mount("/static", StaticFiles(directory=str(PANEL_DIR)), name="static")


@app.get("/")
async def root():
    """Корень ведет на меню."""
    return RedirectResponse(url="/menu")


@app.get("/menu")
async def get_menu():
    """Красивая ссылка для меню."""
    return FileResponse(PANEL_DIR / "menu.html")


@app.get("/panel")
async def get_panel():
    """Красивая ссылка для панели."""
    return FileResponse(PANEL_DIR / "panel.html")


@app.get("/about")
async def get_about():
    """Красивая ссылка для страницы о проекте."""
    return FileResponse(PANEL_DIR / "about.html")


@app.get("/favicon.ico")
async def favicon():
    """Глушим 404 на favicon."""
    return Response(status_code=204)


@app.on_event("startup")
async def startup_event():
    print("[*] Geryon Recon — starting up...")
    db.init_db()
    load_from_db()
    print(f"[+] loaded {len(BOTS)} bots, {len(TASKS)} tasks from DB")


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)