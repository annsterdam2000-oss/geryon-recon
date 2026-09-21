# agent/modules/telegram.py
import re

import requests


TELEGRAM_TIMEOUT = 8
TELEGRAM_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                      "AppleWebKit/537.36 (KHTML, like Gecko) " \
                      "Chrome/120.0 Safari/537.36"


def module_telegram(target: str) -> dict:
    result = {"target": target}

    # --- нормализация ---
    username = target.strip()
    username = re.sub(r"^https?://t\.me/", "", username, flags=re.IGNORECASE)
    username = username.lstrip("@").strip().split("?")[0].split("/")[0]

    if not re.match(r"^[a-zA-Z0-9_]{5,32}$", username):
        return {
            "error": "invalid telegram username "
                     "(5-32 chars, allowed: a-z A-Z 0-9 _)"
        }

    result["username"] = username
    result["url"] = f"https://t.me/{username}"

    # --- запрос ---
    try:
        r = requests.get(
            result["url"],
            timeout=TELEGRAM_TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": TELEGRAM_USER_AGENT},
        )
        result["http_status"] = r.status_code
        result["final_url"] = r.url
    except requests.exceptions.Timeout:
        return {**result, "error": "timeout"}
    except requests.exceptions.ConnectionError:
        return {**result, "error": "connection error"}
    except Exception as e:
        return {**result, "error": str(e)}

    html = r.text or ""

    # --- редирект на главную = нет аккаунта ---
    if r.url.rstrip("/") in ("https://t.me", "https://telegram.org"):
        result["exists"] = False
        return result

    # --- мета-теги ---
    def _meta(prop: str):
        m = re.search(
            rf'<meta[^>]+property="{re.escape(prop)}"[^>]+content="([^"]*)"',
            html,
            re.IGNORECASE,
        )
        return m.group(1).strip() if m else None

    title = _meta("og:title")
    description = _meta("og:description")
    image = _meta("og:image")

    # --- заглушка "нет аккаунта" ---
    if not title and "If you have Telegram" in html:
        result["exists"] = False
        return result

    result["exists"] = True
    result["title"] = title
    result["description"] = description
    result["image"] = image

    # --- тип ---
    desc_lower = (description or "").lower()
    if "channel" in desc_lower or "канал" in desc_lower:
        result["kind"] = "channel"
    elif "bot" in desc_lower or "бот" in desc_lower:
        result["kind"] = "bot"
    elif "group" in desc_lower or "группа" in desc_lower or "чат" in desc_lower:
        result["kind"] = "group"
    else:
        result["kind"] = "user"

    return result