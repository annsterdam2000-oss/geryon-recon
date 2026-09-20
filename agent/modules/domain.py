# agent/modules/domain.py
import socket
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import dns.resolver
import requests
import whois as whois_lib


MAX_SUBDOMAINS_TO_CHECK = 50
SUBDOMAIN_WORKERS = 10
SUBDOMAIN_TIMEOUT = 5


def module_domain(target: str) -> dict:
    target = target.strip().lower()
    target = target.replace("https://", "").replace("http://", "").split("/")[0]

    result = {"target": target, "_timings": {}}

    # --- WHOIS ---
    t0 = time.time()
    try:
        w = whois_lib.whois(target)
        result["whois"] = {
            "registrar": w.registrar,
            "creation_date": _date_to_str(w.creation_date),
            "expiration_date": _date_to_str(w.expiration_date),
            "updated_date": _date_to_str(w.updated_date),
            "name_servers": _ns_to_list(w.name_servers),
            "status": w.status if isinstance(w.status, list) else ([w.status] if w.status else []),
            "emails": w.emails if isinstance(w.emails, list) else ([w.emails] if w.emails else []),
            "org": w.org,
            "country": w.country,
        }
    except Exception as e:
        result["whois_error"] = str(e)
    result["_timings"]["whois"] = round(time.time() - t0, 2)

    # --- DNS ---
    t0 = time.time()
    dns_data = {}
    for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]:
        try:
            answers = dns.resolver.resolve(target, rtype, lifetime=5)
            if rtype == "MX":
                dns_data[rtype] = sorted([f"{r.preference} {str(r.exchange).rstrip('.')}" for r in answers])
            elif rtype == "SOA":
                dns_data[rtype] = [str(answers[0])]
            else:
                dns_data[rtype] = sorted([str(r).rstrip(".") for r in answers])
        except Exception:
            dns_data[rtype] = []
    result["dns"] = dns_data
    result["_timings"]["dns"] = round(time.time() - t0, 2)

    # --- Поддомены через crt.sh ---
    t0 = time.time()
    subdomains = []
    try:
        r = requests.get(
            f"https://crt.sh/?q=%25.{target}&output=json",
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if r.status_code == 200:
            subs = set()
            for entry in r.json():
                name = entry.get("name_value", "")
                for line in name.split("\n"):
                    line = line.strip().lower()
                    if line and "*" not in line:
                        subs.add(line)
            subdomains = sorted(subs)[:200]
            result["subdomains"] = subdomains
            result["subdomains_count"] = len(subs)
        else:
            result["subdomains"] = []
            result["subdomains_error"] = f"crt.sh HTTP {r.status_code}"
    except Exception as e:
        result["subdomains"] = []
        result["subdomains_error"] = str(e)
    result["_timings"]["crt.sh"] = round(time.time() - t0, 2)

    # --- Проверка поддоменов на живость (параллельно) ---
    t0 = time.time()
    subs_to_check = subdomains[:MAX_SUBDOMAINS_TO_CHECK]
    if subs_to_check:
        live_subs = _check_subdomains_alive(subs_to_check)
        result["subdomains_live"] = live_subs
        result["subdomains_live_count"] = sum(1 for s in live_subs if s["alive"])
    else:
        result["subdomains_live"] = []
        result["subdomains_live_count"] = 0
    result["_timings"]["subdomains_check"] = round(time.time() - t0, 2)

    # --- HTTP-заголовки основного домена ---
    t0 = time.time()
    try:
        r = requests.get(
            f"http://{target}",
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        result["http"] = {
            "status": r.status_code,
            "server": r.headers.get("Server"),
            "powered_by": r.headers.get("X-Powered-By"),
            "final_url": r.url,
        }
    except Exception as e:
        result["http"] = {"error": str(e)}
    result["_timings"]["http"] = round(time.time() - t0, 2)

    # --- SSL-сертификат ---
    t0 = time.time()
    result["ssl"] = _get_ssl_info(target)
    result["_timings"]["ssl"] = round(time.time() - t0, 2)

    return result


# ---------- Поддомены ----------

def _check_subdomains_alive(subdomains: list) -> list:
    """Проверяет поддомены параллельно: HTTP + IP."""
    results = []
    with ThreadPoolExecutor(max_workers=SUBDOMAIN_WORKERS) as ex:
        future_map = {ex.submit(_check_one_subdomain, sub): sub for sub in subdomains}
        for fut in as_completed(future_map):
            try:
                results.append(fut.result())
            except Exception:
                sub = future_map[fut]
                results.append({"host": sub, "alive": False, "error": "exception"})

    # сортируем: живые сначала, потом по алфавиту
    results.sort(key=lambda x: (not x.get("alive"), x.get("host", "")))
    return results


def _check_one_subdomain(host: str) -> dict:
    info = {"host": host, "alive": False, "http_status": None, "ip": None, "redirect": None}

    # IP через A-запись
    try:
        answers = dns.resolver.resolve(host, "A", lifetime=3)
        info["ip"] = str(answers[0])
    except Exception:
        pass

    # HTTP-запрос
    for scheme in ("https", "http"):
        try:
            r = requests.get(
                f"{scheme}://{host}",
                timeout=SUBDOMAIN_TIMEOUT,
                allow_redirects=False,
                headers={"User-Agent": "Mozilla/5.0"},
                verify=False,
            )
            info["alive"] = True
            info["http_status"] = r.status_code
            info["scheme"] = scheme
            if r.status_code in (301, 302, 303, 307, 308):
                info["redirect"] = r.headers.get("Location")
            break
        except requests.exceptions.SSLError:
            continue
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.Timeout:
            info["error"] = "timeout"
            return info
        except Exception:
            continue

    return info


# ---------- SSL ----------

def _get_ssl_info(host: str) -> dict:
    """Получает SSL-сертификат через прямое соединение."""
    info = {}
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with socket.create_connection((host, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                if not cert:
                    # если verify_mode=CERT_NONE, getpeercert() возвращает пустой dict
                    # пробуем через бинарный формат
                    der = ssock.getpeercert(binary_form=True)
                    if der:
                        info["error"] = "cert parse failed (binary only)"
                        return info
                    info["error"] = "no cert returned"
                    return info

                # issuer
                issuer = dict(x[0] for x in cert.get("issuer", []))
                info["issuer"] = {
                    "commonName": issuer.get("commonName"),
                    "organizationName": issuer.get("organizationName"),
                    "countryName": issuer.get("countryName"),
                }
                # subject
                subject = dict(x[0] for x in cert.get("subject", []))
                info["subject"] = {
                    "commonName": subject.get("commonName"),
                    "organizationName": subject.get("organizationName"),
                }
                # даты
                info["not_before"] = cert.get("notBefore")
                info["not_after"] = cert.get("notAfter")
                # SAN
                san = []
                for typ, val in cert.get("subjectAltName", []):
                    san.append(f"{typ}:{val}")
                info["san"] = san[:50]  # ограничим
                info["san_count"] = len(san)
    except Exception as e:
        info["error"] = str(e)
    return info


# ---------- Утилиты ----------

def _date_to_str(d):
    if not d:
        return None
    if isinstance(d, list):
        d = d[0]
    try:
        return d.isoformat()
    except AttributeError:
        return str(d)


def _ns_to_list(ns):
    if not ns:
        return []
    if isinstance(ns, str):
        return [ns.lower()]
    return sorted([str(n).lower().rstrip(".") for n in ns])