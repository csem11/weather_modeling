"""
Collect NWS Climate (CLI) reports and append to data/nws_daily.csv.

Scrapes https://forecast.weather.gov/product.php?site=...&product=CLI&issuedby=...
for each configured station and parses daily max/min temp and precipitation.
- Default: latest report only (one row per station).
- With --historical: follows version links (1, 2, 3, ...) to fetch many days per station.
"""

from weather_modeling.cli.collect_nws import main

if __name__ == "__main__":
    main()
