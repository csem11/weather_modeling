"""Data sources: Open-Meteo API, NWS scraping, AAA gas prices."""

from weather_modeling.sources.open_meteo import (
    collect_forecast,
    collect_historical,
    fetch_archive,
    fetch_archive_for_cities,
    fetch_forecast,
    fetch_forecast_for_cities,
)
from weather_modeling.sources.nws import (
    load_nws_data,
    save_nws_data,
    scrape_all,
    scrape_all_historical,
    scrape_one,
    scrape_one_versions,
)
from weather_modeling.sources.gas import fetch_all_gas_prices, save_gas_to_data

__all__ = [
    "collect_forecast",
    "collect_historical",
    "fetch_archive",
    "fetch_archive_for_cities",
    "fetch_forecast",
    "fetch_forecast_for_cities",
    "load_nws_data",
    "save_nws_data",
    "scrape_all",
    "scrape_all_historical",
    "scrape_one",
    "scrape_one_versions",
    "fetch_all_gas_prices",
    "save_gas_to_data",
]
