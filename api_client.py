"""Open-Meteo API client for forecast and historical weather data."""

from datetime import date, timedelta
from typing import Any

import requests

from config import (
    ARCHIVE_BASE,
    CITIES,
    DAILY_VARS,
    FORECAST_BASE,
    HOURLY_VARS,
)


def fetch_forecast(
    latitude: float,
    longitude: float,
    *,
    forecast_days: int = 16,
    past_days: int = 0,
    timezone: str = "auto",
) -> dict[str, Any]:
    """Fetch hourly and daily forecast from Open-Meteo Forecast API."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": HOURLY_VARS,
        "daily": DAILY_VARS,
        "forecast_days": forecast_days,
        "past_days": past_days,
        "timezone": timezone,
    }
    r = requests.get(FORECAST_BASE, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_archive(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
    *,
    timezone: str = "auto",
) -> dict[str, Any]:
    """Fetch historical hourly and daily weather from Open-Meteo Archive API."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": HOURLY_VARS,
        "daily": DAILY_VARS,
        "timezone": timezone,
    }
    r = requests.get(ARCHIVE_BASE, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_forecast_for_cities(
    cities: list[tuple[str, float, float]] | None = None,
    forecast_days: int = 16,
    past_days: int = 7,
) -> dict[str, dict[str, Any]]:
    """Fetch forecast for multiple cities. Returns {city_name: response}."""
    cities = cities or CITIES
    result = {}
    for name, lat, lon in cities:
        try:
            result[name] = fetch_forecast(lat, lon, forecast_days=forecast_days, past_days=past_days)
        except requests.RequestException as e:
            result[name] = {"error": str(e)}
    return result


def fetch_archive_for_cities(
    start_date: date,
    end_date: date,
    cities: list[tuple[str, float, float]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Fetch historical data for multiple cities. Returns {city_name: response}."""
    cities = cities or CITIES
    result = {}
    for name, lat, lon in cities:
        try:
            result[name] = fetch_archive(lat, lon, start_date, end_date)
        except requests.RequestException as e:
            result[name] = {"error": str(e)}
    return result
