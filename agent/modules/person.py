# agent/modules/person.py
"""
Поиск по ФИО в открытых источниках.
Только публичные данные: DuckDuckGo, Wikipedia, GitHub, Habr.
"""
import re
import time
import urllib.parse

import requests


def module_person(target: str) -> dict:
    target = target.strip()
    if not target or len(target) < 3:
        return {"error": "слишком короткое ФИО"}

    result = {
        "target": target,
        "mentions": [],
        "sources": {},
        "_timings": {},
    }

    # Транслитерация для поиска ников
    translit = _translit(target)
    variants = _generate_variants(target, translit)
    result["variants"] = variants

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0 Safari/537.36",
        "Accept-Language": "ru,en;q=0.9",
    })

    # --- 1. DuckDuckGo HTML ---
    t0 = time.time()
    try:
        q = urllib.parse.quote_plus(target)
        r = session.get(
            f"https://html.duckduckgo.com/html/?q={q}",
            timeout=15,
        )
        # Парсим ссылки
        links = re.findall(r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>', r.text)
        for href, title in links[:20]:
            # DDG оборачивает ссылки в редирект — вытаскиваем uddg
            if "uddg=" in href:
                href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
            result["mentions"].append({
                "source": "DuckDuckGo",
                "title": _clean_html(title),
                "url": href,
            })
    except Exception as e:
        result["sources"]["duckduckgo_error"] = str(e)
    result["_timings"]["duckduckgo"] = round(time.time() - t0, 2)

    # --- 2. Wikipedia ---
    t0 = time.time()
    try:
        r = session.get(
            "https://ru.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": target,
                "format": "json",
                "srlimit": 10,
            },
            timeout=10,
        )
        data = r.json()
        for item in data.get("query", {}).get("search", []):
            result["mentions"].append({
                "source": "Wikipedia",
                "title": _clean_html(item.get("title", "")),
                "url": "https://ru.wikipedia.org/wiki/" + urllib.parse.quote(item.get("title", "").replace(" ", "_")),
                "snippet": _clean_html(item.get("snippet", "")),
            })
    except Exception as e:
        result["sources"]["wikipedia_error"] = str(e)
    result["_timings"]["wikipedia"] = round(time.time() - t0, 2)

    # --- 3. GitHub users ---
    t0 = time.time()
    try:
        # пробуем варианты ников
        for variant in variants[:4]:
            r = session.get(
                f"https://api.github.com/search/users?q={urllib.parse.quote(variant)}",
                timeout=10,
                headers={"Accept": "application/vnd.github+json"},
            )
            if r.status_code != 200:
                continue
            for item in r.json().get("items", [])[:5]:
                result["mentions"].append({
                    "source": "GitHub",
                    "title": item.get("login"),
                    "url": item.get("html_url"),
                })
    except Exception as e:
        result["sources"]["github_error"] = str(e)
    result["_timings"]["github"] = round(time.time() - t0, 2)

    # --- 4. Habr ---
    t0 = time.time()
    try:
        q = urllib.parse.quote_plus(target)
        r = session.get(
            f"https://habr.com/ru/search/?q={q}&target_type=posts&order=relevance",
            timeout=10,
        )
        # Ищем ссылки на профили
        users = set(re.findall(r'href="(/ru/users/[^/"]+)"', r.text))
        for u in list(users)[:10]:
            result["mentions"].append({
                "source": "Habr",
                "title": u.split("/")[-2],
                "url": f"https://habr.com{u}/",
            })
    except Exception as e:
        result["sources"]["habr_error"] = str(e)
    result["_timings"]["habr"] = round(time.time() - t0, 2)

    result["mentions_count"] = len(result["mentions"])
    return result


def _translit(s: str) -> str:
    """Простая транслитерация рус → лат."""
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    return "".join(table.get(c.lower(), c) for c in s)


def _generate_variants(name: str, translit: str) -> list:
    """Генерирует возможные ник-варианты из ФИО."""
    name = name.strip()
    translit = translit.strip()
    parts_ru = name.split()
    parts_en = translit.split()

    variants = set()

    # ivanivanov
    if parts_en:
        variants.add("".join(parts_en).lower())
    # ivan.ivanov
    if len(parts_en) >= 2:
        variants.add(f"{parts_en[0]}.{parts_en[1]}".lower())
    # iivanov
    if len(parts_en) >= 2:
        variants.add(f"{parts_en[0][0]}{parts_en[1]}".lower())
    # ivanov
    if parts_en:
        variants.add(parts_en[0].lower())

    return [v for v in variants if len(v) >= 3]


def _clean_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()