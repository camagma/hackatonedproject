import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta


try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


WEATHER_MODIFIERS = {
    "Clear": {"Flood": 0, "Wildfire": 8, "Mountain / Forest": 0, "Urban Area": 0, "Missing Person": 0, "Other": 0},
    "Rain": {"Flood": 20, "Wildfire": -5, "Mountain / Forest": 12, "Urban Area": 5, "Missing Person": 8, "Other": 5},
    "Storm": {"Flood": 35, "Wildfire": 5, "Mountain / Forest": 25, "Urban Area": 15, "Missing Person": 20, "Other": 15},
    "Snow": {"Flood": 12, "Wildfire": -8, "Mountain / Forest": 30, "Urban Area": 10, "Missing Person": 22, "Other": 18},
    "Fog": {"Flood": 8, "Wildfire": 0, "Mountain / Forest": 15, "Urban Area": 10, "Missing Person": 15, "Other": 8},
    "Extreme Heat": {"Flood": 5, "Wildfire": 40, "Mountain / Forest": 12, "Urban Area": 12, "Missing Person": 10, "Other": 5},
}

WEATHER_ICONS = {"Clear": "☀️", "Rain": "🌧️", "Storm": "⛈️", "Snow": "❄️", "Fog": "🌫️", "Extreme Heat": "🔥"}
WEATHER_TTL_MINUTES = 20
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

WMO_WEATHER_LABELS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    56: "Freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Rain showers",
    81: "Rain showers",
    82: "Violent rain showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm with hail",
}


def classify_weather_snapshot(current: dict) -> str:
    code = int(current.get("weather_code") or 0)
    temp = float(current.get("temperature_2m") or 0)
    apparent = float(current.get("apparent_temperature") or temp)
    precipitation = float(current.get("precipitation") or 0)
    rain = float(current.get("rain") or 0)
    showers = float(current.get("showers") or 0)
    snowfall = float(current.get("snowfall") or 0)
    wind_gusts = float(current.get("wind_gusts_10m") or 0)
    wind_speed = float(current.get("wind_speed_10m") or 0)
    if apparent >= 35 or temp >= 37:
        return "Extreme Heat"
    if code in {95, 96, 99} or wind_gusts >= 70 or wind_speed >= 55:
        return "Storm"
    if code in {45, 48}:
        return "Fog"
    if code in {71, 73, 75, 77, 85, 86} or snowfall > 0:
        return "Snow"
    if code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82} or precipitation > 0 or rain > 0 or showers > 0:
        return "Rain"
    return "Clear"


def fallback_weather_snapshot(lat=None, lon=None, error: str | None = None) -> dict:
    return {
        "category": "Clear",
        "label": "Weather unavailable",
        "source": "fallback",
        "updated_at": datetime.now().isoformat(),
        "lat": lat,
        "lon": lon,
        "error": error or "Weather API unavailable",
    }


def fetch_open_meteo_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": f"{float(lat):.6f}",
        "longitude": f"{float(lon):.6f}",
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "precipitation",
            "rain",
            "showers",
            "snowfall",
            "weather_code",
            "cloud_cover",
            "wind_speed_10m",
            "wind_gusts_10m",
            "is_day",
        ]),
        "timezone": "auto",
    }
    if HAS_REQUESTS:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=6)
        response.raise_for_status()
        payload = response.json()
    else:
        encoded = urllib.parse.urlencode(params)
        with urllib.request.urlopen(f"{OPEN_METEO_URL}?{encoded}", timeout=6) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    current = payload.get("current") or {}
    category = classify_weather_snapshot(current)
    code = int(current.get("weather_code") or 0)
    return {
        "category": category,
        "label": WMO_WEATHER_LABELS.get(code, f"WMO {code}"),
        "source": "Open-Meteo",
        "updated_at": datetime.now().isoformat(),
        "observed_at": current.get("time"),
        "lat": float(lat),
        "lon": float(lon),
        "weather_code": code,
        "temperature_c": current.get("temperature_2m"),
        "apparent_temperature_c": current.get("apparent_temperature"),
        "precipitation_mm": current.get("precipitation"),
        "rain_mm": current.get("rain"),
        "snowfall_cm": current.get("snowfall"),
        "cloud_cover_pct": current.get("cloud_cover"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_gusts_kmh": current.get("wind_gusts_10m"),
        "is_day": current.get("is_day"),
    }


def weather_snapshot_stale(case: dict, max_age_minutes: int = WEATHER_TTL_MINUTES) -> bool:
    weather = case.get("weather") or {}
    if weather.get("category") not in WEATHER_MODIFIERS:
        return True
    if weather.get("source") == "fallback" or weather.get("label") == "Weather unavailable":
        return True
    try:
        updated = datetime.fromisoformat(weather.get("updated_at", ""))
        if datetime.now() - updated > timedelta(minutes=max_age_minutes):
            return True
    except Exception:
        return True
    try:
        if abs(float(weather.get("lat")) - float(case.get("lat"))) > 0.002:
            return True
        if abs(float(weather.get("lon")) - float(case.get("lon"))) > 0.002:
            return True
    except Exception:
        return True
    return False
