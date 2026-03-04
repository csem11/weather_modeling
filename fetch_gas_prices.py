#!/usr/bin/env python3
"""
Fetch AAA gas prices (national average + all 50 states + DC) and save to project data storage.

Uses the same data/ directory and CSV pattern as the rest of the project:
  - data/gas_national.csv  (one row per fetch date: national averages by time period and fuel type)
  - data/gas_state.csv     (one row per fetch date per state: regular, mid_grade, premium, diesel)

Usage (from project root):
  python fetch_gas_prices.py
  python fetch_gas_prices.py --data-dir data
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from weather_modeling.sources.gas import fetch_all_gas_prices, save_gas_to_data


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch AAA gas prices and save to data/ CSVs.")
    ap.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Data directory (default: data)",
    )
    args = ap.parse_args()

    data_dir = args.data_dir.resolve()
    data = fetch_all_gas_prices()
    national_path, state_path = save_gas_to_data(data, data_dir)

    print(f"  Wrote {national_path} ({len(pd.read_csv(national_path))} national rows)")
    print(f"  Wrote {state_path} ({len(pd.read_csv(state_path))} state rows)")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
