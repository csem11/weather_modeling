"""Collect NWS Climate (CLI) reports and append to data/nws_daily.csv."""

import sys
from pathlib import Path

from weather_modeling.config import NWS_MAX_VERSIONS_HISTORICAL
from weather_modeling.sources.nws import load_nws_data, save_nws_data, scrape_all, scrape_all_historical


def main() -> None:
    historical = "--historical" in sys.argv or "-H" in sys.argv
    data_dir = Path("data")
    if historical:
        print(f"Scraping NWS CLI reports (historical, up to {NWS_MAX_VERSIONS_HISTORICAL} versions per station)...")
        df = scrape_all_historical(max_versions_per_station=NWS_MAX_VERSIONS_HISTORICAL)
    else:
        print("Scraping NWS Climate (CLI) reports for all configured stations (latest only)...")
        df = scrape_all()
    if df.empty:
        print("No data parsed. NWS may be unavailable or report format changed.")
        return
    out_path = save_nws_data(df, data_dir)
    n_stations = df["city"].nunique()
    n_rows = len(df)
    print(f"Saved/updated {out_path} ({n_rows} rows, {n_stations} stations)")
    total = load_nws_data(data_dir)
    if not total.empty:
        print(f"Total rows in nws_daily.csv: {len(total)} (dates: {total['report_date'].min()} to {total['report_date'].max()})")
