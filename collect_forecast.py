"""
Collect and save forecast data from Open-Meteo for all configured cities.

Fetches hourly and daily forecast (plus past days) and writes to
data/forecast_hourly.csv and data/forecast_daily.csv.
"""

from pathlib import Path

from config import FORECAST_COLLECTION_DAYS
from data_collector import collect_forecast, save_forecast


def main() -> None:
    data_dir = Path("data")
    print(f"Fetching forecast ({FORECAST_COLLECTION_DAYS} days ahead + 7 past days) for all cities...")
    hourly, daily = collect_forecast(
        forecast_days=FORECAST_COLLECTION_DAYS,
        past_days=7,
    )
    if hourly.empty or daily.empty:
        raise SystemExit("No forecast data returned. Check API and cities.")

    save_forecast(hourly, daily, data_dir)
    print(f"Saved forecast to {data_dir}/forecast_hourly.csv and {data_dir}/forecast_daily.csv")
    print(f"  Hourly rows: {len(hourly)}, Daily rows: {len(daily)}")


if __name__ == "__main__":
    main()
