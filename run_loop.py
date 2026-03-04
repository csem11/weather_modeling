"""
Long-running loop: every N hours, check if today's gas price data exists and fetch if not.

Used by: python main.py run [--interval HOURS] [--data-dir PATH]
"""

import sys
import time
from datetime import date, datetime
from pathlib import Path

from config import GAS_CHECK_INTERVAL_HOURS


def _today_gas_collected(data_dir: Path) -> bool:
    """Return True if gas_national.csv contains a row for today's date."""
    path = data_dir / "gas_national.csv"
    if not path.exists():
        return False
    import pandas as pd
    df = pd.read_csv(path)
    if df.empty or "date" not in df.columns:
        return False
    df["date"] = pd.to_datetime(df["date"]).dt.date
    today = date.today()
    return today in df["date"].values


def _parse_run_args() -> tuple[Path, float]:
    """Parse sys.argv for run command: --interval HOURS, --data-dir PATH."""
    data_dir = Path("data")
    interval_hours = GAS_CHECK_INTERVAL_HOURS
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--interval" and i + 1 < len(args):
            try:
                interval_hours = float(args[i + 1])
            except ValueError:
                pass
            i += 2
        elif args[i] == "--data-dir" and i + 1 < len(args):
            data_dir = Path(args[i + 1])
            i += 2
        else:
            i += 1
    return data_dir, interval_hours


def run_indefinitely(data_dir: Path | str = "data", interval_hours: float | None = None) -> None:
    """
    Run forever: every interval_hours, check if today's gas data is in data/gas_national.csv.
    If not, run the gas price fetch and save. Then sleep until next check.
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    interval_hours = interval_hours if interval_hours is not None else GAS_CHECK_INTERVAL_HOURS
    interval_seconds = max(60, interval_hours * 3600)

    print(f"Run loop started: check gas data every {interval_hours} hours (every {interval_seconds:.0f}s)")
    print("Press Ctrl+C to stop.")
    print()

    while True:
        try:
            now = datetime.now().isoformat(timespec="seconds")
            if _today_gas_collected(data_dir):
                print(f"[{now}] Today's gas price data already present. Next check in {interval_hours} hours.")
            else:
                print(f"[{now}] Today's gas data missing. Fetching...")
                from fetch_gas_prices import fetch_all_gas_prices, save_gas_to_data
                data = fetch_all_gas_prices()
                save_gas_to_data(data, data_dir)
                print(f"[{datetime.now().isoformat(timespec='seconds')}] Gas data saved.")
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"[{datetime.now().isoformat(timespec='seconds')}] Error: {e}. Retrying in {interval_hours} hours.")
            time.sleep(interval_seconds)
