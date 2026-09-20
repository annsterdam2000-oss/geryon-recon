# server/notify.py
"""
Отправка уведомлений о завершённых задачах в Discord.
"""
import os

import requests


DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")


# Цвета для embed (Discord использует десятичные значения)
COLOR_DONE = 0x2ECC71      # зелёный
COLOR_FAILED = 0xE74C3C    # красный
COLOR_RUNNING = 0x3498DB   # синий


def send_discord_embed(title: str, description: str = "", fields: list = None,
                       color: int = COLOR_DONE, footer: str = "OSINTicus"):
    """Отправляет embed в Discord. Тихо логирует ошибки, не ломает сервер."""
    if not DISCORD_WEBHOOK_URL:
        print("[!] DISCORD_WEBHOOK_URL не задан, уведомления отключены")
        return

    embed = {
        "title": title,
        "color": color,
        "footer": {"text": footer},
    }
    if description:
        embed["description"] = description
    if fields:
        embed["fields"] = [
            {"name": f["name"], "value": f["value"], "inline": f.get("inline", False)}
            for f in fields
        ]

    try:
        r = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"embeds": [embed]},
            timeout=10,
        )
        if r.status_code not in (200, 204):
            print(f"[!] discord notify: HTTP {r.status_code} — {r.text[:200]}")
    except Exception as e:
        print(f"[!] discord notify failed: {e}")


def notify_task_done(task: dict):
    """Формирует и отправляет уведомление по завершённой задаче."""
    try:
        _notify_task_done(task)
    except Exception as e:
        print(f"[!] notify_task_done error: {e}")


def _notify_task_done(task: dict):
    task_type = task.get("task_type", "?")
    target = task.get("target", "?")
    status = task.get("status", "?")
    result = task.get("result", {}) or {}

    color = COLOR_DONE if status == "done" else COLOR_FAILED

    icon = "✅" if status == "done" else "❌"
    title = f"{icon} {task_type}: {target}"
    if status == "failed":
        title = f"❌ {task_type}: {target} — failed"

    fields = []

    # Время выполнения
    started = task.get("started_at")
    finished = task.get("finished_at")
    if started and finished:
        elapsed = round(finished - started, 2)
        fields.append({"name": "Время", "value": f"{elapsed}с", "inline": True})

    # Ошибка
    if task.get("error"):
        fields.append({
            "name": "Ошибка",
            "value": str(task["error"])[:1000],
            "inline": False,
        })

    # Результат — по типам задач
    if task_type == "email":
        _fields_email(result, fields)
    elif task_type == "email_reg":
        _fields_email_reg(result, fields)
    elif task_type == "domain":
        _fields_domain(result, fields)
    elif task_type == "username":
        _fields_username(result, fields)
    elif task_type == "ip":
        _fields_ip(result, fields)
    elif task_type == "phone":
        _fields_phone(result, fields)
    elif task_type == "person":
        _fields_person(result, fields)

    send_discord_embed(title=title, fields=fields, color=color)


# ---------- Форматтеры по типам задач ----------

def _fields_email(r, fields):
    if r.get("mx"):
        fields.append({"name": "MX", "value": ", ".join(r["mx"][:5]), "inline": False})
    if r.get("a_records"):
        fields.append({"name": "A-записи", "value": ", ".join(r["a_records"][:5]), "inline": False})
    g = r.get("gravatar")
    if g is True:
        fields.append({"name": "Gravatar", "value": "✅ есть", "inline": True})
    elif g is False:
        fields.append({"name": "Gravatar", "value": "❌ нет", "inline": True})


def _fields_email_reg(r):
    pass


def _fields_email_reg(r, fields):
    reg = r.get("registered", []) or []
    total = r.get("total_checked", 0)
    fields.append({
        "name": "Зарегистрирован",
        "value": f"{len(reg)} из {total}" if total else str(len(reg)),
        "inline": True,
    })
    if reg:
        fields.append({
            "name": "Сайты",
            "value": ", ".join(reg[:15])[:1000],
            "inline": False,
        })


def _fields_domain(r, fields):
    w = r.get("whois", {}) or {}
    if w.get("registrar"):
        fields.append({"name": "Регистратор", "value": w["registrar"], "inline": True})
    subs = r.get("subdomains", []) or []
    if subs:
        fields.append({"name": "Поддоменов", "value": str(r.get("subdomains_count", len(subs))), "inline": True})
    h = r.get("http", {}) or {}
    if h.get("status"):
        fields.append({"name": "HTTP", "value": f"{h['status']} {h.get('server') or ''}".strip(), "inline": True})


def _fields_username(r, fields):
    found = r.get("found_count", 0)
    total = r.get("total", 0)
    fields.append({
        "name": "Найдено",
        "value": f"{found} из {total}",
        "inline": True,
    })
    # список найденных сайтов
    results = r.get("results", []) or []
    found_sites = [x.get("site") for x in results if x.get("status") == "found" and x.get("site")]
    if found_sites:
        fields.append({
            "name": "Сайты",
            "value": ", ".join(found_sites[:20])[:1000],
            "inline": False,
        })


def _fields_ip(r, fields):
    g = r.get("geo", {}) or {}
    n = r.get("network", {}) or {}
    if g.get("country"):
        fields.append({"name": "Страна", "value": f"{g['country']} ({g.get('country_code', '?')})", "inline": True})
    if g.get("city"):
        fields.append({"name": "Город", "value": g["city"], "inline": True})
    if n.get("isp"):
        fields.append({"name": "ISP", "value": n["isp"], "inline": False})
    if n.get("as"):
        fields.append({"name": "ASN", "value": n["as"], "inline": False})
    ptr = r.get("ptr", []) or []
    if ptr:
        fields.append({"name": "PTR", "value": ", ".join(ptr[:5]), "inline": False})


def _fields_phone(r, fields):
    if r.get("country_code"):
        fields.append({"name": "Страна", "value": f"+{r['country_code']}", "inline": True})
    if r.get("carrier"):
        fields.append({"name": "Оператор", "value": r["carrier"], "inline": True})
    if r.get("number_type"):
        fields.append({"name": "Тип", "value": r["number_type"], "inline": True})
    if r.get("region"):
        fields.append({"name": "Регион", "value": r["region"], "inline": False})
    if r.get("is_valid") is not None:
        v = "✅ валидный" if r["is_valid"] else "❌ невалидный"
        fields.append({"name": "Валидность", "value": v, "inline": True})


def _fields_person(r, fields):
    mentions = r.get("mentions", []) or []
    fields.append({"name": "Упоминаний", "value": str(len(mentions)), "inline": True})
    # источники
    sources = {}
    for m in mentions:
        s = m.get("source", "?")
        sources[s] = sources.get(s, 0) + 1
    if sources:
        s_text = ", ".join(f"{k}: {v}" for k, v in sources.items())
        fields.append({"name": "Источники", "value": s_text[:1000], "inline": False})
    # топ-3 ссылки
    top = mentions[:3]
    if top:
        links = "\n".join(f"[{m.get('title', '?')}]({m.get('url', '#')})" for m in top)
        fields.append({"name": "Топ ссылок", "value": links[:1000], "inline": False})