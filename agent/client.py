# agent/client.py
# ☄ Arc Warden's split — клиент отщепляется, говорит с сервером, возвращается.
import platform
import socket
import time

import requests


class ServerClient:
    def __init__(self, server_url: str, modules: list):
        self.server = server_url
        self.modules = modules
        self.bot_id = None
        self.agent_name = None
        self.meepo_num = None

    def get_info(self):
        return {
            "hostname": socket.gethostname(),
            "os": f"{platform.system()} {platform.release()}",
            "user": platform.node(),
            "modules": self.modules,
        }

    def register(self):
        info = self.get_info()
        while True:
            try:
                r = requests.post(f"{self.server}/register", json=info, timeout=10)
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
        r = requests.post(f"{self.server}/heartbeat/{self.bot_id}", timeout=10)
        r.raise_for_status()
        return r.json()

    def send_result(self, task_id: str, status: str, result: dict, error: str = ""):
        try:
            requests.post(
                f"{self.server}/result",
                json={
                    "task_id": task_id,
                    "bot_id": self.bot_id,
                    "status": status,
                    "result": result,
                    "error": error,
                },
                timeout=10,
            )
        except Exception as e:
            print(f"[!] result send failed: {e}")