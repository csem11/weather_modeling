"""Collect weather data from Open-Meteo and build datasets for modeling. All temperatures in °F."""

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

def _c_to_f(c: float) -> float:
    """Celsius to Fahrenheit."""
    return c * 9 / 5 + 32


def _c_to_f_series(s: pd.Series) -> pd.Series:
    """Convert Celsius series to Fahrenheit (preserves NaN)."""
    return s.astype(float) * 9 / 5 + 32

from api_client import fetch_archive_for_cities, fetch_forecast_for_cities
from config import CITIES, HISTORICAL_DAYS


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
    cities = cities or CITIES
    # Archive API can have a few days delay; use yesterday as end_date to be safe
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


def build_training_data(
    daily_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a flat table: one row per (city, date) with features only (no targets).
    Features: lags, hourly aggregates, calendar — all from Open-Meteo. No NWS columns.
    Add targets separately via add_nws_targets() for training.
    """
    if daily_df.empty or hourly_df.empty:
        return pd.DataFrame()

    daily = daily_df.reset_index()
    hourly = hourly_df.reset_index()
    hourly["date"] = pd.to_datetime(hourly["time"]).dt.date

    hourly_agg = (
        hourly.groupby(["city", "date"], as_index=False)
        .agg(
            hourly_temp_mean=("temperature_2m", "mean"),
            hourly_temp_std=("temperature_2m", "std"),
            hourly_temp_min=("temperature_2m", "min"),
            hourly_temp_max=("temperature_2m", "max"),
            hourly_precip_sum=("precipitation", "sum"),
            hourly_cloud_mean=("cloud_cover", "mean"),
            hourly_pressure_mean=("pressure_msl", "mean"),
        )
        .fillna(0)
    )

    daily["date"] = pd.to_datetime(daily["date"]).dt.date
    merged = daily.merge(hourly_agg, on=["city", "date"], how="left")
    merged = merged.sort_values(["city", "date"]).reset_index(drop=True)

    # Convert all temperatures to Fahrenheit (Open-Meteo provides °C)
    for col in ["temperature_2m_max", "temperature_2m_min"]:
        if col in merged.columns:
            merged[col] = _c_to_f_series(merged[col])
    for col in ["hourly_temp_mean", "hourly_temp_std", "hourly_temp_min", "hourly_temp_max"]:
        if col in merged.columns:
            merged[col] = _c_to_f_series(merged[col])

    for lag in [1, 2, 3]:
        merged[f"lag{lag}_max"] = merged.groupby("city")["temperature_2m_max"].shift(lag)
        merged[f"lag{lag}_min"] = merged.groupby("city")["temperature_2m_min"].shift(lag)

    merged["day_of_year"] = pd.to_datetime(merged["date"]).dt.dayofyear
    merged["month"] = pd.to_datetime(merged["date"]).dt.month
    merged["latitude"] = merged["latitude"].astype(float)
    merged["longitude"] = merged["longitude"].astype(float)

    return merged


def add_nws_targets(
    df: pd.DataFrame,
    nws_df: pd.DataFrame,
    date_col: str = "date",
    city_col: str = "city",
) -> pd.DataFrame:
    """
    Add next-day high/low targets from NWS only (no NWS features).
    For each row (city, date), target = NWS obs for (city, date+1).
    Adds target_next_day_high, target_next_day_low. Rows without NWS data get NaN.
    """
    if df.empty or nws_df.empty:
        df = df.copy()
        df["target_next_day_high"] = None
        df["target_next_day_low"] = None
        return df

    need = ["report_date", "city", "max_temp_c", "min_temp_c"]
    nws = nws_df[[c for c in need if c in nws_df.columns]].copy()
    if "report_date" not in nws.columns or "max_temp_c" not in nws.columns:
        df = df.copy()
        df["target_next_day_high"] = None
        df["target_next_day_low"] = None
        return df

    # NWS provides °C; convert to °F for targets
    nws = nws.copy()
    nws["next_date"] = pd.to_datetime(nws["report_date"]).dt.date
    nws["target_next_day_high"] = _c_to_f_series(nws["max_temp_c"])
    nws["target_next_day_low"] = _c_to_f_series(nws["min_temp_c"])
    nws = nws[["city", "next_date", "target_next_day_high", "target_next_day_low"]]

    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col]).dt.date
    out["next_date"] = out[date_col] + timedelta(days=1)
    out = out.merge(nws, on=[city_col, "next_date"], how="left")
    out = out.drop(columns=["next_date"], errors="ignore")
    return out


def save_data(hourly: pd.DataFrame, daily: pd.DataFrame, directory: str | Path = "data") -> None:
    """Save collected hourly and daily DataFrames to CSV."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    if not hourly.empty:
        hourly.to_csv(path / "hourly.csv", index=True)
    if not daily.empty:
        daily.to_csv(path / "daily.csv", index=True)


def save_forecast(hourly: pd.DataFrame, daily: pd.DataFrame, directory: str | Path = "data") -> None:
    """Save forecast hourly and daily DataFrames to CSV."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    if not hourly.empty:
        hourly.to_csv(path / "forecast_hourly.csv", index=True)
    if not daily.empty:
        daily.to_csv(path / "forecast_daily.csv", index=True)


def load_forecast(directory: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load forecast hourly and daily CSVs from directory."""
    path = Path(directory)
    hourly_path = path / "forecast_hourly.csv"
    daily_path = path / "forecast_daily.csv"
    hourly = (
        pd.read_csv(hourly_path, index_col=0, parse_dates=True)
        if hourly_path.exists()
        else pd.DataFrame()
    )
    daily = (
        pd.read_csv(daily_path, index_col=0, parse_dates=True)
        if daily_path.exists()
        else pd.DataFrame()
    )
    if not daily.empty:
        daily.index = pd.to_datetime(daily.index)
    return hourly, daily


def load_data(directory: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load hourly and daily CSVs from directory."""
    path = Path(directory)
    hourly_path = path / "hourly.csv"
    daily_path = path / "daily.csv"

    hourly = pd.read_csv(hourly_path, index_col=0, parse_dates=True) if hourly_path.exists() else pd.DataFrame()
    daily = pd.read_csv(daily_path, index_col=0, parse_dates=True) if daily_path.exists() else pd.DataFrame()
    if not daily.empty and daily.index.name == "date":
        daily.index = pd.to_datetime(daily.index)
    return hourly, daily


def save_gas_data(
    national_df: pd.DataFrame,
    state_df: pd.DataFrame,
    directory: str | Path = "data",
) -> None:
    """Save gas price DataFrames to data/gas_national.csv and data/gas_state.csv."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    if not national_df.empty:
        national_df.to_csv(path / "gas_national.csv", index=False)
    if not state_df.empty:
        state_df.to_csv(path / "gas_state.csv", index=False)


def load_gas_data(directory: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load gas price CSVs from directory. Returns (national_df, state_df)."""
    path = Path(directory)
    national = (
        pd.read_csv(path / "gas_national.csv")
        if (path / "gas_national.csv").exists()
        else pd.DataFrame()
    )
    state = (
        pd.read_csv(path / "gas_state.csv")
        if (path / "gas_state.csv").exists()
        else pd.DataFrame()
    )
    if not national.empty and "date" in national.columns:
        national["date"] = pd.to_datetime(national["date"]).dt.date
    if not state.empty and "date" in state.columns:
        state["date"] = pd.to_datetime(state["date"]).dt.date
    return national, state


def merge_nws_into_daily(
    daily_df: pd.DataFrame,
    nws_df: pd.DataFrame,
    date_col: str = "date",
    city_col: str = "city",
) -> pd.DataFrame:
    """
    Left-merge NWS observed temps into a daily DataFrame by date and city.
    Adds columns: nws_max_temp_c, nws_min_temp_c, nws_precip_in (when present).
    Expects daily_df to have date and city; nws_df from load_nws_data() has report_date, city, max_temp_c, min_temp_c, precip_in.
    """
    if daily_df.empty or nws_df.empty:
        return daily_df
    daily = daily_df.reset_index() if date_col not in daily_df.columns and daily_df.index.name == date_col else daily_df.copy()
    if date_col not in daily.columns:
        return daily
    need = ["report_date", "city", "max_temp_c", "min_temp_c", "precip_in"]
    nws = nws_df[[c for c in need if c in nws_df.columns]].copy()
    nws = nws.rename(columns={"report_date": date_col, "max_temp_c": "nws_max_temp_c", "min_temp_c": "nws_min_temp_c", "precip_in": "nws_precip_in"})
    nws[date_col] = pd.to_datetime(nws[date_col]).dt.date
    daily[date_col] = pd.to_datetime(daily[date_col]).dt.date
    merged = daily.merge(nws, on=[date_col, city_col], how="left")
    return merged
