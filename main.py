"""
Weather data collection: Open-Meteo, NWS climate reports, and AAA gas prices.

Usage:
  python main.py daily   # Collect all data for the day: forecast + NWS (latest) + gas (recommended once per day)
  python main.py collect # Fetch and save Open-Meteo forecast to data/forecast_*.csv
  python main.py nws     # Scrape NWS Climate (CLI) reports into data/nws_daily.csv
  python main.py nws --historical   # Historical backfill via version links (run separately, not daily)
  python main.py run     # Run indefinitely: every N hours check for today's gas data, fetch if missing
"""

from weather_modeling.cli.main import main

if __name__ == "__main__":
    main()
