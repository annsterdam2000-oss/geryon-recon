# agent/modules/sysinfo.py
# ☄ Третий глаз Гериона — смотрит внутрь железа, а не наружу.
#
# Источник: LibreHardwareMonitor (LHM), web-сервер на 8085.
# Ищем сенсоры по SensorId — он стабильный и однозначный.

import requests

LHM_URL = "http://localhost:8085/data.json"
TIMEOUT = 3


def _flatten(node, out):
    if not isinstance(node, dict):
        return
    text = node.get("Text", "")
    value = node.get("Value", "")
    sid = node.get("SensorId", "")

    if value and value not in ("", "-") and text not in ("Sensor", "Value"):
        out.append({
            "id": sid,
            "sensor": text,
            "value": value,
            "type": node.get("Type", ""),
        })

    for child in (node.get("Children") or []):
        _flatten(child, out)


def _by_id(sensors, sensor_id):
    for s in sensors:
        if s["id"] == sensor_id:
            return s["value"]
    return None


def collect():
    try:
        r = requests.get(LHM_URL, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"available": False, "reason": str(e)}

    sensors = []
    _flatten(data, sensors)

    # ---------- CPU ----------
    cpu_load = _by_id(sensors, "/amdcpu/0/load/0")           # CPU Total
    cpu_temp = _by_id(sensors, "/amdcpu/0/temperature/2")    # Core (Tctl/Tdie)

    # ---------- GPU ----------
    # Ищем первый GPU в дереве — у тебя /gpu-nvidia/0, но мало ли
    gpu_prefix = None
    for s in sensors:
        if s["id"].startswith("/gpu") and s["id"].count("/") >= 3:
            # /gpu-nvidia/0/...
            parts = s["id"].split("/")
            gpu_prefix = "/".join(parts[:3])  # /gpu-nvidia/0
            break

    gpu_load = None
    gpu_temp = None
    if gpu_prefix:
        gpu_load = _by_id(sensors, f"{gpu_prefix}/load/0")
        gpu_temp = _by_id(sensors, f"{gpu_prefix}/temperature/0")

    # ---------- RAM ----------
    # /ram/data/0 — Memory Used, /ram/data/1 — Memory Available (Total Memory нода)
    ram_used = _by_id(sensors, "/ram/data/0")
    ram_avail = _by_id(sensors, "/ram/data/1")

    # ---------- Диск ----------
    # /ssd/0/data/31 — Free Space, /ssd/0/data/32 — Total Space
    disk_free = _by_id(sensors, "/ssd/0/data/31")
    disk_total = _by_id(sensors, "/ssd/0/data/32")
    disk_used_pct = _by_id(sensors, "/ssd/0/load/30")  # Used Space в %

    return {
        "available": True,
        "cpu_load": cpu_load,
        "cpu_temp": cpu_temp,
        "gpu_load": gpu_load,
        "gpu_temp": gpu_temp,
        "ram_used": ram_used,
        "ram_avail": ram_avail,
        "disk_free": disk_free,
        "disk_total": disk_total,
        "disk_used_pct": disk_used_pct,
    }