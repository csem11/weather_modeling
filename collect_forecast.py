"""
Collect and save forecast data from Open-Meteo for all configured cities.

Fetches hourly and daily forecast (plus past days) and writes to
data/forecast_hourly.csv and data/forecast_daily.csv.
"""

from weather_modeling.cli.collect_forecast import main

if __name__ == "__main__":
    main()
