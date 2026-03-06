"""
Weather data collection: Open-Meteo, NWS climate reports, and AAA gas prices.

Usage:
  python main.py run     # Run indefinitely: full daily collection every 12h (forecast + NWS + gas). Use --interval N to change.
  python main.py daily   # Collect once: forecast + NWS (latest) + gas
  python main.py collect # Fetch and save Open-Meteo forecast to data/forecast_*.csv
  python main.py nws     # Scrape NWS Climate (CLI) reports into data/nws_daily.csv
  python main.py nws --historical   # Historical backfill via version links (run separately)
"""

from weather_modeling.cli.main import main

if __name__ == "__main__":
    main()
