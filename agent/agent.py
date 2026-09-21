# agent/agent.py
import argparse
import threading
import time

from client import ServerClient
from modules import MODULE_FUNCS


SERVER = "http://127.0.0.1:5555"
HEARTBEAT_INTERVAL = 2
MODULES = [
    "email",
    "email_reg",
    "domain",
    "http_check",
    "ip",
    "phone",
    "person",
    "telegram",
]


def handle_task(client: ServerClient, task: dict):
    task_id = task["task_id"]
    task_type = task["task_type"]

    print(f"[>] task {task_id}: {task_type} -> "
          f"{task.get('target', task.get('url', ''))}")
    t0 = time.time()

    func = MODULE_FUNCS.get(task_type)
    if func is None:
        status = "failed"
        result = {}
        error = f"unsupported task type: {task_type}"
    else:
        try:
            if task_type == "http_check":
                result = func(task)
            else:
                result = func(task["target"])
            status = "failed" if result.get("error") else "done"
            error = result.get("error", "")
        except Exception as e:
            status = "failed"
            result = {}
            error = str(e)

    elapsed = round(time.time() - t0, 2)
    print(f"[=] task {task_id} -> {status} за {elapsed}с")
    client.send_result(task_id, status, result, error)


def agent_loop(name: str = "agent"):
    client = ServerClient(SERVER, MODULES)
    client.register()

    while True:
        try:
            data = client.heartbeat()
            if data.get("task"):
                handle_task(client, data["task"])
        except Exception as e:
            print(f"[{name}] [!] heartbeat failed: {e}")
        time.sleep(HEARTBEAT_INTERVAL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1,
                        help="сколько агентов запустить (потоков)")
    args = parser.parse_args()

    if args.count <= 1:
        agent_loop("agent")
    else:
        threads = []
        for i in range(args.count):
            t = threading.Thread(target=agent_loop, args=(f"agent{i+1}",), daemon=True)
            t.start()
            threads.append(t)
            time.sleep(0.3)
        print(f"[+] запущено {args.count} агентов")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("[!] остановлено")


if __name__ == "__main__":
    main()