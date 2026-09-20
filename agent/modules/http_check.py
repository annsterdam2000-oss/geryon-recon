# agent/modules/http_check.py
import requests

HTTP_TIMEOUT = 5


def module_http_check(task: dict) -> dict:
    url = task["url"]
    found_codes = task.get("found_codes", [200])
    not_found_codes = task.get("not_found_codes", [404])
    site = task.get("site", "")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    })

    try:
        r = session.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
        code = r.status_code
        if code in found_codes:
            status = "found"
        elif code in not_found_codes:
            status = "not_found"
        else:
            status = "unknown"
        return {
            "site": site,
            "url": url,
            "status": status,
            "http_code": code,
        }
    except requests.exceptions.Timeout:
        return {"site": site, "url": url, "status": "unknown", "error": "timeout"}
    except requests.exceptions.ConnectionError:
        return {"site": site, "url": url, "status": "unknown", "error": "connection error"}
    except Exception as e:
        return {"site": site, "url": url, "status": "unknown", "error": str(e)}
    finally:
        session.close()