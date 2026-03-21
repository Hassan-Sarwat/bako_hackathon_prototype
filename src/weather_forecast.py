"""Weather data module using Open-Meteo API for Munich.

Fetches historical and forecast weather data and caches it in the
weather_data SQLite table. Uses urllib (no extra dependencies).

Open-Meteo is free, no API key required.
Munich coordinates: lat=48.14, lon=11.58
"""

import json
import sqlite3
import urllib.request
import urllib.error
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "bakery.db"

MUNICH_LAT = 48.14
MUNICH_LON = 11.58

HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _fetch_json(url: str) -> dict | None:
    """Fetch JSON from URL, return None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BakoBakery/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return None


def fetch_historical_weather(start_date: str, end_date: str) -> list[dict]:
    """Fetch historical weather from Open-Meteo archive for Munich.

    Returns list of dicts with keys:
        date, temperature_max, temperature_min, temperature_mean,
        precipitation_mm, weather_code
    """
    params = (
        f"?latitude={MUNICH_LAT}&longitude={MUNICH_LON}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
        f"precipitation_sum,weather_code"
        f"&timezone=Europe%2FBerlin"
    )
    data = _fetch_json(HISTORICAL_URL + params)
    if not data or "daily" not in data:
        return []

    daily = data["daily"]
    dates = daily.get("time", [])
    results = []
    for i, d in enumerate(dates):
        results.append({
            "date": d,
            "temperature_max": daily["temperature_2m_max"][i],
            "temperature_min": daily["temperature_2m_min"][i],
            "temperature_mean": daily["temperature_2m_mean"][i],
            "precipitation_mm": daily["precipitation_sum"][i],
            "weather_code": daily["weather_code"][i],
        })
    return results


def fetch_forecast_weather(days: int = 3) -> list[dict]:
    """Fetch weather forecast from Open-Meteo for Munich.

    Returns same format as fetch_historical_weather.
    """
    params = (
        f"?latitude={MUNICH_LAT}&longitude={MUNICH_LON}"
        f"&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
        f"precipitation_sum,weather_code"
        f"&timezone=Europe%2FBerlin"
        f"&forecast_days={days}"
    )
    data = _fetch_json(FORECAST_URL + params)
    if not data or "daily" not in data:
        return []

    daily = data["daily"]
    dates = daily.get("time", [])
    results = []
    for i, d in enumerate(dates):
        results.append({
            "date": d,
            "temperature_max": daily["temperature_2m_max"][i],
            "temperature_min": daily["temperature_2m_min"][i],
            "temperature_mean": daily["temperature_2m_mean"][i],
            "precipitation_mm": daily["precipitation_sum"][i],
            "weather_code": daily["weather_code"][i],
        })
    return results


def sync_weather_data(start_date: str, end_date: str) -> int:
    """Fetch weather from Open-Meteo and cache in weather_data table.

    For past dates uses historical API, for today/future uses forecast API.
    Returns number of rows synced.
    """
    today = date.today()
    count = 0
    conn = _get_connection()
    cursor = conn.cursor()

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    # Historical portion
    hist_end = min(end, today - timedelta(days=1))
    if start <= hist_end:
        records = fetch_historical_weather(start.isoformat(), hist_end.isoformat())
        for r in records:
            cursor.execute(
                "INSERT INTO weather_data "
                "(weather_date, temperature_max, temperature_min, temperature_mean, "
                "precipitation_mm, weather_code) VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(weather_date) DO UPDATE SET "
                "temperature_max=excluded.temperature_max, "
                "temperature_min=excluded.temperature_min, "
                "temperature_mean=excluded.temperature_mean, "
                "precipitation_mm=excluded.precipitation_mm, "
                "weather_code=excluded.weather_code",
                (r["date"], r["temperature_max"], r["temperature_min"],
                 r["temperature_mean"], r["precipitation_mm"], r["weather_code"]),
            )
            count += 1

    # Forecast portion
    if end >= today:
        forecast_days = (end - today).days + 1
        records = fetch_forecast_weather(min(forecast_days, 16))
        for r in records:
            rd = date.fromisoformat(r["date"])
            if rd < start or rd > end:
                continue
            cursor.execute(
                "INSERT INTO weather_data "
                "(weather_date, temperature_max, temperature_min, temperature_mean, "
                "precipitation_mm, weather_code) VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(weather_date) DO UPDATE SET "
                "temperature_max=excluded.temperature_max, "
                "temperature_min=excluded.temperature_min, "
                "temperature_mean=excluded.temperature_mean, "
                "precipitation_mm=excluded.precipitation_mm, "
                "weather_code=excluded.weather_code",
                (r["date"], r["temperature_max"], r["temperature_min"],
                 r["temperature_mean"], r["precipitation_mm"], r["weather_code"]),
            )
            count += 1

    conn.commit()
    conn.close()
    return count


def get_cached_weather(start_date: str, end_date: str) -> list[dict]:
    """Read weather data from the local cache (weather_data table)."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT weather_date, temperature_max, temperature_min, temperature_mean, "
        "precipitation_mm, weather_code "
        "FROM weather_data WHERE weather_date BETWEEN ? AND ? ORDER BY weather_date",
        (start_date, end_date),
    )
    items = []
    for row in cursor.fetchall():
        items.append({
            "date": row["weather_date"],
            "temperature_max": row["temperature_max"],
            "temperature_min": row["temperature_min"],
            "temperature_mean": row["temperature_mean"],
            "precipitation_mm": row["precipitation_mm"],
            "weather_code": row["weather_code"],
        })
    conn.close()
    return items
