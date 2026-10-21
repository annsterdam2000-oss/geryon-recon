# agent/modules/email.py
import hashlib
import re

import dns.resolver
import requests


def module_email(target: str) -> dict:
    target = target.strip().lower()
    result = {"target": target}

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", target):
        return {"error": "invalid email syntax"}

    local, domain = target.split("@", 1)
    result["local"] = local
    result["domain"] = domain

    # --- MX-записи ---
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        result["mx"] = sorted([str(r.exchange).rstrip(".") for r in answers])
    except Exception as e:
        result["mx"] = []
        result["mx_error"] = str(e)

    # --- A-записи ---
    try:
        answers = dns.resolver.resolve(domain, "A", lifetime=5)
        result["a_records"] = [str(r) for r in answers]
    except Exception:
        result["a_records"] = []

    # --- Gravatar ---
    try:
        h = hashlib.md5(target.encode()).hexdigest()
        r = requests.get(
            f"https://www.gravatar.com/avatar/{h}?d=404",
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        
        if r.status_code == 200:
            result["gravatar"] = True
        elif r.status_code == 404:
            result["gravatar"] = False
        else:
            result["gravatar"] = None
            result["gravatar_http"] = r.status_code
            result["gravatar_error"] = f"unexpected HTTP {r.status_code}"
            
    except requests.exceptions.Timeout:
        result["gravatar"] = None
        result["gravatar_error"] = "timeout"
    except Exception as e:
        result["gravatar"] = None
        result["gravatar_error"] = str(e)

    return result