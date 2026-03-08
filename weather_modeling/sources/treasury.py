"""
Fetch U.S. Treasury daily yield curve data (CSV) from home.treasury.gov.

Data: Constant Maturity Treasury (CMT) rates by maturity (1, 3, 6 mo; 1, 2, 3, 5, 7, 10, 20, 30 yr).
Source: https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve
CSV is fetched by month; backfill by iterating months from a start year to current.
"""

from __future__ import annotations

import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from weather_modeling.config import TREASURY_CSV_BASE
from weather_modeling.storage.io import load_treasury_data, save_treasury_data

REQUEST_TIMEOUT = 45
REQUEST_DELAY = 0.6  # between month requests for backfill

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,text/plain,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
}


def _csv_url_for_month(year: int, month: int) -> str:
    """Build CSV download URL for a single month (e.g. 2024, 1 -> .../202401)."""
    yyyymm = f"{year}{month:02d}"
    return f"{TREASURY_CSV_BASE}/{yyyymm}?type=daily_treasury_yield_curve&_format=csv"


def fetch_month(year: int, month: int) -> pd.DataFrame:
    """
    Fetch daily treasury yield curve CSV for one month. Returns DataFrame with date column and rate columns.
    Empty DataFrame on failure or if no data.
    """
    url = _csv_url_for_month(year, month)
    try:
        r = requests.get(url, headers=_HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
    except requests.RequestException:
        return pd.DataFrame()

    text = r.text.strip()
    # Skip if response looks like HTML (e.g. 403 page)
    if not text or "<!DOCTYPE" in text[:50].upper() or "<HTML" in text[:50].upper():
        return pd.DataFrame()
    if "Date" not in text and "date" not in text:
        return pd.DataFrame()

    try:
        df = pd.read_csv(pd.io.common.StringIO(text))
    except Exception:
        return pd.DataFrame()

    if df.empty:
        return df

    # Normalize date column (Treasury often uses "Date")
    for col in ("Date", "date"):
        if col in df.columns:
            df = df.rename(columns={col: "date"})
            break
    if "date" not in df.columns:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.dropna(subset=["date"])
    return df


def fetch_range(start_date: date, end_date: date | None = None) -> pd.DataFrame:
    """
    Fetch daily treasury yield data for all months in [start_date, end_date].
    end_date defaults to today. Uses a short delay between months.
    """
    end_date = end_date or date.today()
    if start_date > end_date:
        return pd.DataFrame()

    frames = []
    y, m = start_date.year, start_date.month
    end_y, end_m = end_date.year, end_date.month
    while (y, m) <= (end_y, end_m):
        df = fetch_month(y, m)
        if not df.empty:
            frames.append(df)
        time.sleep(REQUEST_DELAY)
        m += 1
        if m > 12:
            m = 1
            y += 1

    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    return out


def fetch_latest() -> pd.DataFrame:
    """Fetch current month and previous month to get latest data."""
    today = date.today()
    if today.month == 1:
        start = date(today.year - 1, 12, 1)
    else:
        start = date(today.year, today.month - 1, 1)
    return fetch_range(start, today)


def save_treasury_to_data(df: pd.DataFrame, directory: Path | str = "data") -> Path:
    """
    Append treasury yield data to data/treasury_yield_curve.csv. Dedupes by date.
    Returns path to the CSV file.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "treasury_yield_curve.csv"

    if df.empty:
        return path

    if "date" not in df.columns:
        return path

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date

    if path.exists():
        existing = pd.read_csv(path)
        existing["date"] = pd.to_datetime(existing["date"]).dt.date
        new_dates = set(df["date"].astype(str))
        existing = existing[~existing["date"].astype(str).isin(new_dates)]
        combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    else:
        combined = df

    save_treasury_data(combined, directory)
    return path
