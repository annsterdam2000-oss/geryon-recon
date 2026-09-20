# server/server.py
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из папки server/
load_dotenv(Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

import db
from routes.agent import router as agent_router
from routes.panel import router as panel_router
from state import manager, bots_snapshot, tasks_snapshot, load_from_db


PANEL_DIR = Path(__file__).resolve().parent.parent / "panel"

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(PANEL_DIR)), name="static")

app.include_router(agent_router)
app.include_router(panel_router)


@app.on_event("startup")
async def startup():
    db.init_db()
    load_from_db()


@app.on_event("shutdown")
async def shutdown():
    db.close()


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    await ws.send_json({"type": "bots", "bots": bots_snapshot()})
    await ws.send_json({"type": "tasks", "tasks": tasks_snapshot()})
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.get("/", response_class=HTMLResponse)
async def index():
    return (PANEL_DIR / "panel.html").read_text(encoding="utf-8")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5555)