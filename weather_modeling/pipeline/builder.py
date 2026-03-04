"""Build feature tables from Open-Meteo data and attach NWS targets. All temperatures in °F."""

from datetime import timedelta

import pandas as pd


def _c_to_f(c: float) -> float:
    """Celsius to Fahrenheit."""
    return c * 9 / 5 + 32


def _c_to_f_series(s: pd.Series) -> pd.Series:
    """Convert Celsius series to Fahrenheit (preserves NaN)."""
    return s.astype(float) * 9 / 5 + 32


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


def merge_nws_into_daily(
    daily_df: pd.DataFrame,
    nws_df: pd.DataFrame,
    date_col: str = "date",
    city_col: str = "city",
) -> pd.DataFrame:
    """
    Left-merge NWS observed temps into a daily DataFrame by date and city.
    Adds columns: nws_max_temp_c, nws_min_temp_c, nws_precip_in (when present).
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
