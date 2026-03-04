"""
Weather data collection: Open-Meteo, NWS climate reports, and AAA gas prices.

Entrypoint: python -m weather_modeling
Or from repo root: python main.py collect | nws | run
"""

from weather_modeling.cli.main import main

__all__ = ["main"]
