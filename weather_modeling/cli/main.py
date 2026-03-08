"""Dispatch for main.py collect | nws | run | daily | treasury."""

import sys


def main() -> None:
    valid = ("collect", "nws", "run", "daily", "treasury")
    if len(sys.argv) < 2 or sys.argv[1] not in valid:
        print("Usage: python main.py collect | nws | run | daily | treasury")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "collect":
        from weather_modeling.cli.collect_forecast import main as collect_main
        collect_main()
    elif cmd == "nws":
        from weather_modeling.cli.collect_nws import main as nws_main
        nws_main()
    elif cmd == "treasury":
        from weather_modeling.cli.collect_treasury import main as treasury_main
        treasury_main()
    elif cmd == "daily":
        from pathlib import Path
        from weather_modeling.cli.collect_forecast import main as collect_main
        from weather_modeling.cli.collect_nws import main as nws_main
        from weather_modeling.sources.gas import fetch_all_gas_prices, save_gas_to_data
        from weather_modeling.sources.treasury import fetch_latest, save_treasury_to_data
        data_dir = Path("data")
        print("=== Daily collection: forecast, NWS (latest), gas, Treasury ===\n")
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
        print("\n=== Daily collection complete ===")
    else:
        from weather_modeling.cli.run_loop import run_indefinitely, parse_run_args
        data_dir, interval = parse_run_args()
        run_indefinitely(data_dir=data_dir, interval_hours=interval)
