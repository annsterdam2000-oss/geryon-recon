# agent/modules/email_reg.py
"""
Модуль проверки регистраций email через holehe (вызов .exe напрямую).
"""
import os
import re
import subprocess
import time


# Мусорные "сайты", которые regex ловит ошибочно — игнорируем
IGNORE_SITES = {
    "Email",       # из строки "[+] Email used"
    "Rate",        # на всякий случай
    "Mail",
    "Email used",
}


def _find_holehe():
    """Ищет holehe.exe в стандартных местах Windows."""
    candidates = [
        os.path.join(os.environ.get("APPDATA", ""),
                     "Python", "Python314", "Scripts", "holehe.exe"),
        os.path.join(os.environ.get("APPDATA", ""),
                     "Python", "Python313", "Scripts", "holehe.exe"),
        os.path.join(os.environ.get("APPDATA", ""),
                     "Python", "Python312", "Scripts", "holehe.exe"),
        os.path.join(os.environ.get("APPDATA", ""),
                     "Python", "Python311", "Scripts", "holehe.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     "Programs", "Python", "Python314", "Scripts", "holehe.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     "Programs", "Python", "Python313", "Scripts", "holehe.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     "Programs", "Python", "Python312", "Scripts", "holehe.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     "Programs", "Python", "Python311", "Scripts", "holehe.exe"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


def module_email_reg(target: str) -> dict:
    target = target.strip().lower()

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", target):
        return {"error": "invalid email syntax"}

    result = {
        "target": target,
        "registered": [],
        "not_registered": [],
        "unknown": [],
        "rate_limited": [],
    }

    holehe = _find_holehe()
    if not holehe:
        return {"error": "holehe.exe not found"}

    result["_holehe_path"] = holehe
    t0 = time.time()

    try:
        proc = subprocess.run(
            [holehe, target, "--only-used"],
            capture_output=True,
            text=True,
            timeout=300,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return {"error": "holehe timed out (300s)"}
    except Exception as e:
        return {"error": f"holehe call failed: {e}"}

    out = (proc.stdout or "") + "\n" + (proc.stderr or "")

    # Реальный формат holehe: "[+] office365.com"
    line_re = re.compile(r"^\s*\[([+\-x])\]\s+([a-zA-Z0-9._\-]+)", re.MULTILINE)

    def _add(lst, site):
        if site in IGNORE_SITES:
            return
        # дополнительная защита: у реальных сайтов должно быть "."
        # (office365.com, twitter.com), иначе это мусор
        if "." not in site:
            return
        if site not in lst:
            lst.append(site)

    for match in line_re.finditer(out):
        marker = match.group(1)
        site = match.group(2).strip()
        if marker == "+":
            _add(result["registered"], site)
        elif marker == "-":
            _add(result["not_registered"], site)
        elif marker == "x":
            _add(result["rate_limited"], site)

    m = re.search(r"(\d+)\s+websites?\s+checked", out)
    if m:
        result["total_checked"] = int(m.group(1))
    else:
        result["total_checked"] = (
            len(result["registered"])
            + len(result["not_registered"])
            + len(result["rate_limited"])
        )

    result["registered_count"] = len(result["registered"])
    result["_timings"] = {"holehe": round(time.time() - t0, 2)}

    for k in ("registered", "not_registered", "unknown", "rate_limited"):
        result[k].sort()

    if result["registered_count"] == 0 and result["total_checked"] == 0:
        result["_raw_output"] = out[:3000]

    return result