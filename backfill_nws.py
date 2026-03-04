#!/usr/bin/env python3
"""
Backfill NWS Climate (CLI) data for major cities (Kalshi-style daily temperature markets).

Uses long delays and jitter to avoid overloading forecast.weather.gov. Saves after each
station so progress is preserved if interrupted. Run with no args for full backfill.

Ref: https://kalshi.com/category/climate/daily-temperature
"""

import random
import sys
import time
from pathlib import Path

import pandas as pd

from config import (
    NWS_BACKFILL_DELAY_STATIONS,
    NWS_BACKFILL_DELAY_VERSIONS,
    NWS_BACKFILL_JITTER,
    NWS_BACKFILL_MAX_VERSIONS,
    NWS_BACKFILL_STATIONS,
)
from nws_scraper import load_nws_data, save_nws_data, scrape_one_versions


def _jitter(base: float, jitter_max: float) -> float:
    return base + random.uniform(0, jitter_max)


def main() -> None:
    data_dir = Path("data")
    max_versions = NWS_BACKFILL_MAX_VERSIONS
    dry_run = "--dry-run" in sys.argv
    for i, arg in enumerate(sys.argv):
        if arg == "--max-versions" and i + 1 < len(sys.argv):
            max_versions = int(sys.argv[i + 1])
            break

    stations = NWS_BACKFILL_STATIONS
    print(f"Backfilling NWS CLI for {len(stations)} major cities (Kalshi-style).")
    print(f"  Max versions per station: {max_versions}")
    print(f"  Delay between version requests: {NWS_BACKFILL_DELAY_VERSIONS}s + up to {NWS_BACKFILL_JITTER}s jitter")
    print(f"  Delay between stations: {NWS_BACKFILL_DELAY_STATIONS}s + jitter")
    if dry_run:
        print("  [DRY RUN - no requests, no save]")
    print()

    all_rows = []
    for i, (city, site, issuedby) in enumerate(stations, 1):
        delay_ver = _jitter(NWS_BACKFILL_DELAY_VERSIONS, NWS_BACKFILL_JITTER)
        if dry_run:
            print(f"  [{i}/{len(stations)}] Would scrape {city} ({site}/{issuedby}) with delay={delay_ver:.1f}s")
            continue
        print(f"  [{i}/{len(stations)}] {city} ({site}/{issuedby}) ... ", end="", flush=True)
        start = time.perf_counter()
        rows = scrape_one_versions(
            city, site, issuedby,
            max_versions=max_versions,
            delay_seconds=delay_ver,
        )
        elapsed = time.perf_counter() - start
        all_rows.extend(rows)
        print(f"{len(rows)} rows in {elapsed:.0f}s (total {len(all_rows)} rows)", flush=True)
        if all_rows:
            save_nws_data(pd.DataFrame(all_rows), data_dir)
        # Long pause before next station
        pause = _jitter(NWS_BACKFILL_DELAY_STATIONS, NWS_BACKFILL_JITTER)
        if i < len(stations):
            time.sleep(pause)

    if not dry_run and all_rows:
        total = load_nws_data(data_dir)
        print(f"\nDone. nws_daily.csv: {len(total)} rows (dates {total['report_date'].min()} to {total['report_date'].max()})")
    elif dry_run:
        print("\nDry run finished. Run without --dry-run to perform backfill.")


if __name__ == "__main__":
    main()
