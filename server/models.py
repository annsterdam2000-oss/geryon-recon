# server/models.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RegisterReq(BaseModel):
    hostname: str = "unknown"
    os: str = "unknown"
    user: str = "unknown"
    modules: List[str] = []
    hardware: Optional[Dict[str, Any]] = None   # ← новое


class RegisterResp(BaseModel):
    bot_id: str
    agent_name: str
    meepo_num: int


class TaskReq(BaseModel):
    task_type: str
    target: str


class HeartbeatReq(BaseModel):                  # ← новое
    hardware: Optional[Dict[str, Any]] = None


class ResultReq(BaseModel):
    task_id: str
    bot_id: str
    status: str
    result: dict = {}
    error: str = ""