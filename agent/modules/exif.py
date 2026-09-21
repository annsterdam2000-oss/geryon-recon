# agent/modules/exif.py
import io
import os
import tempfile
from fractions import Fraction
from urllib.parse import urlparse

import requests
from PIL import Image, ExifTags


IMAGE_TIMEOUT = 15
IMAGE_MAX_SIZE = 20 * 1024 * 1024  # 20 MB
IMAGE_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                   "AppleWebKit/537.36 (KHTML, like Gecko) " \
                   "Chrome/120.0 Safari/537.36"


def module_exif(target: str) -> dict:
    result = {"target": target}

    target = target.strip()
    if not target:
        return {"error": "empty target"}

    # --- получаем байты изображения ---
    is_url = target.lower().startswith(("http://", "https://"))
    result["source"] = "url" if is_url else "file"

    if is_url:
        data = _download_image(target)
    else:
        data = _read_local_image(target)

    if isinstance(data, dict) and data.get("error"):
        return {**result, **data}

    result["size_bytes"] = len(data)

    # --- открываем через Pillow ---
    try:
        img = Image.open(io.BytesIO(data))
        img.load()  # форсируем загрузку
    except Exception as e:
        return {**result, "error": f"cannot open image: {e}"}

    result["format"] = img.format
    result["mode"] = img.mode
    result["dimensions"] = {"width": img.width, "height": img.height}

    # --- EXIF ---
    try:
        exif = img.getexif()
    except Exception as e:
        return {**result, "error": f"cannot read exif: {e}"}

    if not exif:
        result["has_exif"] = False
        result["raw"] = {}
        return result

    result["has_exif"] = True

    # --- разбор тегов ---
    raw = {}
    for tag_id, value in exif.items():
        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
        # GPSInfo — отдельный вложенный блок
        if tag_name == "GPSInfo":
            continue
        raw[tag_name] = _safe_value(value)
    result["raw"] = raw

    # --- основные поля ---
    result["datetime"] = raw.get("DateTime") or raw.get("DateTimeOriginal")
    result["make"] = raw.get("Make")
    result["model"] = raw.get("Model")
    result["software"] = raw.get("Software")
    result["orientation"] = raw.get("Orientation")

    if result["make"] or result["model"]:
        result["device"] = {
            "make": result["make"],
            "model": result["model"],
        }

    # --- GPS ---
    gps = _extract_gps(exif)
    if gps:
        result["has_gps"] = True
        result["gps"] = gps
    else:
        result["has_gps"] = False

    return result


# ---------- получение файла ----------

def _download_image(url: str) -> bytes | dict:
    try:
        r = requests.get(
            url,
            timeout=IMAGE_TIMEOUT,
            headers={"User-Agent": IMAGE_USER_AGENT},
            stream=True,
        )
        r.raise_for_status()

        # размер
        content_length = r.headers.get("Content-Length")
        if content_length and int(content_length) > IMAGE_MAX_SIZE:
            return {"error": f"image too large ({content_length} bytes)"}

        # читаем с ограничением
        chunks = []
        total = 0
        for chunk in r.iter_content(chunk_size=65536):
            total += len(chunk)
            if total > IMAGE_MAX_SIZE:
                return {"error": f"image too large (>{IMAGE_MAX_SIZE} bytes)"}
            chunks.append(chunk)

        return b"".join(chunks)
    except requests.exceptions.Timeout:
        return {"error": "timeout"}
    except requests.exceptions.ConnectionError:
        return {"error": "connection error"}
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        return {"error": f"HTTP {code}"}
    except Exception as e:
        return {"error": str(e)}


def _read_local_image(path: str) -> bytes | dict:
    if not os.path.isfile(path):
        return {"error": f"file not found: {path}"}
    try:
        size = os.path.getsize(path)
        if size > IMAGE_MAX_SIZE:
            return {"error": f"file too large ({size} bytes)"}
        with open(path, "rb") as f:
            return f.read()
    except Exception as e:
        return {"error": str(e)}


# ---------- GPS ----------

def _extract_gps(exif) -> dict | None:
    try:
        gps_info = exif.get_ifd(ExifTags.IFD.GPSInfo)
    except Exception:
        return None
    if not gps_info:
        return None

    def _to_deg(value):
        d, m, s = value
        return float(d) + float(m) / 60 + float(s) / 3600

    try:
        lat = _to_deg(gps_info[2])
        lon = _to_deg(gps_info[4])
        lat_ref = gps_info.get(1, "N")
        lon_ref = gps_info.get(3, "E")
        if lat_ref != "N":
            lat = -lat
        if lon_ref != "E":
            lon = -lon
        return {
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "altitude": _safe_value(gps_info.get(6)),
            "timestamp": _safe_value(gps_info.get(7)),
            "raw": {
                "lat_ref": lat_ref,
                "lon_ref": lon_ref,
                "lat": _safe_value(gps_info[2]),
                "lon": _safe_value(gps_info[4]),
            },
        }
    except Exception:
        return None


# ---------- утилиты ----------

def _safe_value(v):
    """Приводит EXIF-значение к JSON-сериализуемому виду."""
    if isinstance(v, bytes):
        try:
            return v.decode("utf-8", errors="replace")
        except Exception:
            return repr(v)
    if isinstance(v, Fraction):
        return float(v)
    if isinstance(v, (tuple, list)):
        return [_safe_value(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _safe_value(val) for k, val in v.items()}
    if isinstance(v, (int, float, str, bool)) or v is None:
        return v
    try:
        return str(v)
    except Exception:
        return repr(v)