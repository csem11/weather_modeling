"""
Weather data collection: Open-Meteo, NWS climate reports, AAA gas prices, and Treasury yield curve.

Usage:
  python main.py run       # Run indefinitely: full daily collection every 12h (forecast + NWS + gas)
  python main.py daily     # Collect once: forecast + NWS (latest) + gas
  python main.py collect   # Fetch and save Open-Meteo forecast to data/forecast_*.csv
  python main.py nws       # Scrape NWS Climate (CLI) reports into data/nws_daily.csv
  python main.py nws --historical   # Historical backfill via version links (run separately)
  python main.py treasury  # Fetch latest Treasury yield curve → data/treasury_yield_curve.csv
  python main.py treasury --backfill [--start-year 2020]   # Backfill historical daily data
"""

from weather_modeling.cli.main import main

if __name__ == "__main__":
    main()
