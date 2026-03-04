"""Open-Meteo API client and forecast/historical collection. All temps from API are °C; callers convert to °F."""

from datetime import date, timedelta
from typing import Any

import pandas as pd
import requests

from weather_modeling.config import (
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


def _parse_forecast_response(city: str, lat: float, lon: float, data: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse forecast API response into hourly and daily DataFrames."""
    if "error" in data:
        return pd.DataFrame(), pd.DataFrame()

    hourly = data.get("hourly", {})
    daily = data.get("daily", {})

    if not hourly or not daily:
        return pd.DataFrame(), pd.DataFrame()

    times = pd.to_datetime(hourly["time"])
    hr_df = pd.DataFrame(
        {k: v for k, v in hourly.items() if k != "time"},
        index=times,
    )
    hr_df.index.name = "time"
    hr_df["city"] = city
    hr_df["latitude"] = lat
    hr_df["longitude"] = lon

    day_times = pd.to_datetime(daily["time"])
    day_df = pd.DataFrame(
        {k: v for k, v in daily.items() if k != "time"},
        index=day_times,
    )
    day_df.index.name = "date"
    day_df["city"] = city
    day_df["latitude"] = lat
    day_df["longitude"] = lon

    return hr_df, day_df


def _parse_archive_response(city: str, lat: float, lon: float, data: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse archive API response into hourly and daily DataFrames."""
    if "error" in data:
        return pd.DataFrame(), pd.DataFrame()

    hourly = data.get("hourly", {})
    daily = data.get("daily", {})

    if not hourly or not daily:
        return pd.DataFrame(), pd.DataFrame()

    times = pd.to_datetime(hourly["time"])
    hr_df = pd.DataFrame(
        {k: v for k, v in hourly.items() if k != "time"},
        index=times,
    )
    hr_df.index.name = "time"
    hr_df["city"] = city
    hr_df["latitude"] = lat
    hr_df["longitude"] = lon

    day_times = pd.to_datetime(daily["time"])
    day_df = pd.DataFrame(
        {k: v for k, v in daily.items() if k != "time"},
        index=day_times,
    )
    day_df.index.name = "date"
    day_df["city"] = city
    day_df["latitude"] = lat
    day_df["longitude"] = lon

    return hr_df, day_df


def collect_forecast(
    forecast_days: int = 16,
    past_days: int = 7,
    cities: list[tuple[str, float, float]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Collect forecast data for all cities. Returns (hourly_df, daily_df)."""
    cities = cities or CITIES
    raw = fetch_forecast_for_cities(cities, forecast_days=forecast_days, past_days=past_days)

    hr_frames = []
    day_frames = []
    for name, lat, lon in cities:
        data = raw.get(name, {})
        hr_df, day_df = _parse_forecast_response(name, lat, lon, data)
        if not hr_df.empty:
            hr_frames.append(hr_df)
        if not day_df.empty:
            day_frames.append(day_df)

    hourly = pd.concat(hr_frames, axis=0) if hr_frames else pd.DataFrame()
    daily = pd.concat(day_frames, axis=0) if day_frames else pd.DataFrame()
    return hourly, daily


def collect_historical(
    end_date: date | None = None,
    days: int | None = None,
    cities: list[tuple[str, float, float]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Collect historical weather for training. Returns (hourly_df, daily_df)."""
    from weather_modeling.config import HISTORICAL_DAYS

    cities = cities or CITIES
    end_date = end_date or (date.today() - timedelta(days=1))
    days = days or HISTORICAL_DAYS
    start_date = end_date - timedelta(days=days)

    raw = fetch_archive_for_cities(start_date, end_date, cities)

    hr_frames = []
    day_frames = []
    for name, lat, lon in cities:
        data = raw.get(name, {})
        hr_df, day_df = _parse_archive_response(name, lat, lon, data)
        if not hr_df.empty:
            hr_frames.append(hr_df)
        if not day_df.empty:
            day_frames.append(day_df)

    hourly = pd.concat(hr_frames, axis=0) if hr_frames else pd.DataFrame()
    daily = pd.concat(day_frames, axis=0) if day_frames else pd.DataFrame()
    return hourly, daily
