"""
Collect U.S. Treasury daily yield curve data and save to data/treasury_yield_curve.csv.

- Default: fetch latest data (current + previous month).
- With --backfill: fetch historical daily data from config start year to today.
"""

import sys
from datetime import date
from pathlib import Path

from weather_modeling.config import TREASURY_BACKFILL_START_YEAR
from weather_modeling.sources.treasury import fetch_latest, fetch_range, save_treasury_to_data
from weather_modeling.storage import load_treasury_data


def main() -> None:
    data_dir = Path("data")
    backfill = "--backfill" in sys.argv or "-b" in sys.argv

    # Optional: --start-year YYYY
    start_year = TREASURY_BACKFILL_START_YEAR
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--start-year" and i + 1 < len(args):
            try:
                start_year = int(args[i + 1])
            except ValueError:
                pass
            break

    if backfill:
        start_date = date(start_year, 1, 1)
        print(f"Backfilling Treasury yield curve from {start_date} to today (by month)...")
        df = fetch_range(start_date, date.today())
    else:
        print("Fetching latest Treasury yield curve data (current + previous month)...")
        df = fetch_latest()

    if df.empty:
        print("No data returned. Treasury site may be unavailable or URL changed.")
        return

    path = save_treasury_to_data(df, data_dir)
    print(f"Saved/updated {path} ({len(df)} rows)")
    total = load_treasury_data(data_dir)
    if not total.empty and "date" in total.columns:
        print(f"Total rows in treasury_yield_curve.csv: {len(total)} (dates: {total['date'].min()} to {total['date'].max()})")
