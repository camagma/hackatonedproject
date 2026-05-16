import hashlib
import math
from datetime import datetime


DEFAULT_CENTER = (50.4501, 30.5234)

ADDRESS_PRESETS = {
    "independence square, kyiv": (50.4501, 30.5234),
    "maidan nezalezhnosti, kyiv": (50.4501, 30.5234),
    "olympic stadium, kyiv": (50.4334, 30.5219),
    "podil river station, kyiv": (50.4721, 30.5226),
    "kyiv central station": (50.4412, 30.4882),
    "12 riverside st, springfield": (50.4600, 30.5300),
    "north riverbank, km 4": (50.4685, 30.5155),
    "south bridge, kyiv": (50.3948, 30.5975),
    "hydropark, kyiv": (50.4457, 30.5763),
    "bucharest old town": (44.4325, 26.1025),
}


def haversine(lat1, lon1, lat2, lon2):
    radius = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def case_missing_hours_now(case: dict) -> float:
    try:
        base_hours = float(case.get("time_missing") or 0)
    except Exception:
        base_hours = 0.0
    created_at = case.get("created_at")
    if created_at:
        try:
            elapsed = (datetime.now() - datetime.fromisoformat(created_at)).total_seconds() / 3600
            base_hours += max(0.0, elapsed)
        except Exception:
            pass
    return max(0.0, base_hours)


def dynamic_search_radius_km(case: dict) -> float:
    try:
        base_radius = float(case.get("search_radius_base_km") or case.get("search_radius_km") or 1.0)
    except Exception:
        base_radius = 1.0
    growth_steps = math.floor(case_missing_hours_now(case) * 2)
    return round(base_radius + growth_steps * 5.0, 1)


def geocode_address(address: str, default=DEFAULT_CENTER):
    raw = (address or "").strip()
    key = raw.lower()
    if not key:
        return default
    if key in ADDRESS_PRESETS:
        return ADDRESS_PRESETS[key]
    for known, coords in ADDRESS_PRESETS.items():
        if known in key or key in known:
            return coords
    digest = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
    lat_offset = ((digest % 2000) - 1000) / 100000
    lon_offset = (((digest // 2000) % 2000) - 1000) / 100000
    return default[0] + lat_offset, default[1] + lon_offset
