# server/models.py
from typing import List
from pydantic import BaseModel


class RegisterReq(BaseModel):
    hostname: str = "unknown"
    os: str = "unknown"
    user: str = "unknown"
    modules: List[str] = []


class TaskReq(BaseModel):
    task_type: str
    target: str


class ResultReq(BaseModel):
    task_id: str
    bot_id: str
    status: str
    result: dict = {}
    error: str = ""