# agent/client.py
# ☄ Arc Warden's split — клиент отщепляется, говорит с сервером, возвращается.
import platform
import socket
import time
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from modules import sysinfo

# Ищем .env в папке server, которая находится на уровень выше
dotenv_path = Path(__file__).resolve().parent.parent / "server" / ".env"
load_dotenv(dotenv_path=dotenv_path)


class ServerClient:
    def __init__(self, server_url: str, modules: list):
        self.server = server_url.rstrip("/") # убираем слэш в конце, если есть
        self.modules = modules
        self.bot_id = None
        self.agent_name = None
        self.meepo_num = None
        
        # Берем токен из переменной окружения
        api_token = os.getenv("GERYON_API_TOKEN", "geryon_secret_key_2026")
        self.headers = {"X-API-Key": api_token}

    def get_info(self):
        return {
            "hostname": socket.gethostname(),
            "os": f"{platform.system()} {platform.release()}",
            "user": platform.node(),
            "modules": self.modules,
            "hardware": sysinfo.collect(),
        }

    def register(self):
        info = self.get_info()
        while True:
            try:
                r = requests.post(f"{self.server}/register", json=info, headers=self.headers, timeout=10)
                r.raise_for_status()
                data = r.json()
                self.bot_id = data["bot_id"]
                self.agent_name = data.get("agent_name", self.bot_id)
                self.meepo_num = data.get("meepo_num")
                print(f"[+] little {self.agent_name.lower()} registered "
                      f"modules={self.modules}")
                return self.bot_id
            except Exception as e:
                print(f"[!] register failed: {e}, retry in 3s")
                time.sleep(3)

    def heartbeat(self):
        """Шлём пульс + свежее железо."""
        payload = {"hardware": sysinfo.collect()}
        r = requests.post(
            f"{self.server}/heartbeat/{self.bot_id}",
            json=payload,
            headers=self.headers,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()

    def send_result(self, task_id: str, status: str, result: dict, error: str = ""):
        max_retries = 5
        for attempt in range(max_retries):
            try:
                r = requests.post(
                    f"{self.server}/result",
                    json={
                        "task_id": task_id,
                        "bot_id": self.bot_id,
                        "status": status,
                        "result": result,
                        "error": error,
                    },
                    headers=self.headers,
                    timeout=10,
                )
                if r.status_code == 200:
                    print(f"[+] result {task_id} sent successfully")
                    return
                else:
                    print(f"[!] result send failed (HTTP {r.status_code}), retry {attempt+1}/{max_retries}")
            except Exception as e:
                print(f"[!] result send failed: {e}, retry {attempt+1}/{max_retries}")
            
            if attempt < max_retries - 1:
                time.sleep(3)
        
        print(f"[X] CRITICAL: Could not send result for task {task_id} after {max_retries} attempts")