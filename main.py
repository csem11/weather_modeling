"""
Weather data collection: Open-Meteo, NWS climate reports, and AAA gas prices.

Usage:
  python main.py collect  # Fetch and save Open-Meteo forecast to data/forecast_*.csv
  python main.py nws      # Scrape NWS Climate (CLI) reports into data/nws_daily.csv
  python main.py nws --historical   # Also scrape version links for historical backfill
  python main.py run     # Run indefinitely: every N hours check for today's gas data, fetch if missing
"""

from weather_modeling.cli.main import main

if __name__ == "__main__":
    main()
