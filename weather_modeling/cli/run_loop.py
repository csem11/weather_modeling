"""Long-running loop: run full daily collection (forecast + NWS + gas) every N hours."""

import sys
import time
from datetime import datetime
from pathlib import Path

from weather_modeling.config import RUN_LOOP_INTERVAL_HOURS


def _run_daily_collection(data_dir: Path) -> None:
    """Run one full daily collection: forecast, NWS (latest), gas, Treasury yield curve."""
    from weather_modeling.cli.collect_forecast import main as collect_main
    from weather_modeling.cli.collect_nws import main as nws_main
    from weather_modeling.sources.gas import fetch_all_gas_prices, save_gas_to_data
    from weather_modeling.sources.treasury import fetch_latest, save_treasury_to_data

    collect_main()
    print()
    nws_main()
    print()
    print("Fetching gas prices...")
    data = fetch_all_gas_prices()
    save_gas_to_data(data, data_dir)
    print("Gas data saved.")
    print()
    print("Fetching Treasury yield curve...")
    treasury_df = fetch_latest()
    if not treasury_df.empty:
        save_treasury_to_data(treasury_df, data_dir)
        print("Treasury data saved.")
    else:
        print("No Treasury data returned (skipped).")


def parse_run_args() -> tuple[Path, float]:
    """Parse sys.argv for run command: --interval HOURS, --data-dir PATH."""
    data_dir = Path("data")
    interval_hours = RUN_LOOP_INTERVAL_HOURS
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
    Run forever: every interval_hours, run full daily collection (forecast + NWS latest + gas + Treasury).
    Default interval is 12 hours (twice per day). Override with --interval N.
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    interval_hours = interval_hours if interval_hours is not None else RUN_LOOP_INTERVAL_HOURS
    interval_seconds = max(60, interval_hours * 3600)

    print(f"Run loop started: full daily collection every {interval_hours} hours (every {interval_seconds:.0f}s)")
    print("Press Ctrl+C to stop.")
    print()

    while True:
        try:
            now = datetime.now().isoformat(timespec="seconds")
            print(f"[{now}] Running daily collection (forecast + NWS + gas + Treasury)...")
            _run_daily_collection(data_dir)
            print(f"[{datetime.now().isoformat(timespec='seconds')}] Done. Next run in {interval_hours} hours.")
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"[{datetime.now().isoformat(timespec='seconds')}] Error: {e}. Retrying in {interval_hours} hours.")
            time.sleep(interval_seconds)
