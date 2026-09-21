# agent/modules/geo.py
import re
import time

import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# ⚠️ ЗАМЕНИ на свой email — требование Nominatim
NOMINATIM_USER_AGENT = "osint-panel/0.1 (annsterdam2000@gmail.com)"

GEO_TIMEOUT = 15
NEARBY_RADIUS_M = 100
NEARBY_MAX = 30
NEARBY_CATEGORIES = {
    "amenity": [
        "cafe", "restaurant", "fast_food", "bar", "pub",
        "bank", "atm", "pharmacy", "hospital", "clinic",
        "school", "university", "kindergarten",
        "police", "fire_station", "post_office",
        "fuel", "parking", "bus_station",
    ],
    "shop": ["supermarket", "convenience", "bakery"],
    "public_transport": ["station", "stop_position", "platform"],
    "railway": ["station", "subway_entrance", "tram_stop"],
}

COORD_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")


def module_geo(target: str) -> dict:
    result = {"target": target}

    target = target.strip()
    if not target:
        return {"error": "empty target"}

    # --- определяем: координаты или адрес ---
    m = COORD_RE.match(target)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return {"error": "invalid coordinates range"}
        result["input_type"] = "coords"
        result["lat"] = lat
        result["lon"] = lon
        address = _reverse_geocode(lat, lon)
        result["address"] = address
    else:
        result["input_type"] = "address"
        geo = _forward_geocode(target)
        if geo.get("error"):
            return {**result, "error": geo["error"]}
        result["lat"] = geo["lat"]
        result["lon"] = geo["lon"]
        result["address"] = geo["address"]
        result["display_name"] = geo.get("display_name")
        result["type"] = geo.get("type")

    # --- что рядом (Overpass) ---
    if result.get("lat") is not None and result.get("lon") is not None:
        result["nearby"] = _nearby(result["lat"], result["lon"])

    return result


# ---------- Nominatim ----------

def _nominatim_get(path: str, params: dict) -> dict:
    headers = {"User-Agent": NOMINATIM_USER_AGENT}
    r = requests.get(
        f"{NOMINATIM_URL}{path}",
        params=params,
        headers=headers,
        timeout=GEO_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def _reverse_geocode(lat: float, lon: float) -> dict:
    try:
        data = _nominatim_get("/reverse", {
            "lat": lat, "lon": lon, "format": "json", "zoom": 18,
            "addressdetails": 1, "accept-language": "ru,en",
        })
    except Exception as e:
        return {"error": str(e)}

    if not data or "error" in data:
        return {"error": data.get("error", "not found")}

    a = data.get("address", {})
    return {
        "country": a.get("country"),
        "country_code": a.get("country_code"),
        "region": a.get("state") or a.get("region"),
        "city": a.get("city") or a.get("town") or a.get("village") or a.get("municipality"),
        "suburb": a.get("suburb") or a.get("neighbourhood") or a.get("city_district"),
        "road": a.get("road"),
        "house_number": a.get("house_number"),
        "postcode": a.get("postcode"),
        "display_name": data.get("display_name"),
        "type": data.get("type"),
    }


def _forward_geocode(query: str) -> dict:
    try:
        data = _nominatim_get("/search", {
            "q": query, "format": "json", "limit": 1,
            "addressdetails": 1, "accept-language": "ru,en",
        })
    except Exception as e:
        return {"error": str(e)}

    if not data:
        return {"error": "address not found"}

    first = data[0]
    a = first.get("address", {})
    return {
        "lat": float(first["lat"]),
        "lon": float(first["lon"]),
        "display_name": first.get("display_name"),
        "type": first.get("type"),
        "address": {
            "country": a.get("country"),
            "country_code": a.get("country_code"),
            "region": a.get("state") or a.get("region"),
            "city": a.get("city") or a.get("town") or a.get("village") or a.get("municipality"),
            "suburb": a.get("suburb") or a.get("neighbourhood") or a.get("city_district"),
            "road": a.get("road"),
            "house_number": a.get("house_number"),
            "postcode": a.get("postcode"),
        },
    }


# ---------- Overpass (что рядом) ----------

def _nearby(lat: float, lon: float) -> list:
    filters = []
    for key, values in NEARBY_CATEGORIES.items():
        for v in values:
            filters.append(f'node["{key}"="{v}"](around:{NEARBY_RADIUS_M},{lat},{lon});')
            filters.append(f'way["{key}"="{v}"](around:{NEARBY_RADIUS_M},{lat},{lon});')

    query = f"""
    [out:json][timeout:15];
    (
      {''.join(filters)}
    );
    out center {NEARBY_MAX};
    """

    headers = {
        "User-Agent": NOMINATIM_USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    try:
        r = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers=headers,
            timeout=GEO_TIMEOUT + 10,
        )
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.HTTPError as e:
        # отдельно ловим 429 (rate limit) и 5xx (перегрузка)
        code = e.response.status_code if e.response is not None else "?"
        if code == 429:
            return [{"error": "overpass rate limit (429) — подожди и повтори"}]
        if 500 <= int(code) < 600:
            return [{"error": f"overpass server error ({code}) — попробуй позже"}]
        return [{"error": f"overpass HTTP {code}: {e}"}]
    except Exception as e:
        return [{"error": str(e)}]

    items = []
    for el in data.get("elements", [])[:NEARBY_MAX]:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:ru") or tags.get("name:en")
        if not name:
            continue

        el_lat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        el_lon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        distance = None
        if el_lat and el_lon:
            distance = round(_haversine(lat, lon, el_lat, el_lon), 1)

        category = None
        subtype = None
        for key in NEARBY_CATEGORIES:
            if key in tags:
                category = key
                subtype = tags[key]
                break

        items.append({
            "name": name,
            "category": category,
            "subtype": subtype,
            "distance_m": distance,
            "lat": el_lat,
            "lon": el_lon,
        })

    items.sort(key=lambda x: x["distance_m"] if x["distance_m"] is not None else 1e9)
    return items