"""Configuration: API base URLs and city coordinates for data collection."""

# Open-Meteo API (no API key required for non-commercial use)
FORECAST_BASE = "https://api.open-meteo.com/v1/forecast"
# Historical data: use archive subdomain (see https://open-meteo.com/en/docs/historical-weather-api)
ARCHIVE_BASE = "https://archive-api.open-meteo.com/v1/archive"

# Major US cities: predictions are produced for these only
MAJOR_US_CITIES = [
    ("New York", 40.7128, -74.0060),
    ("Los Angeles", 34.0522, -118.2437),
    ("Chicago", 41.8781, -87.6298),
    ("Houston", 29.7604, -95.3698),
    ("Phoenix", 33.4484, -112.0740),
    ("Philadelphia", 39.9526, -75.1652),
    ("San Antonio", 29.4241, -98.4936),
    ("San Diego", 32.7157, -117.1611),
    ("Dallas", 32.7767, -96.7970),
    ("San Jose", 37.3382, -121.8863),
    ("Austin", 30.2672, -97.7431),
    ("Jacksonville", 30.3322, -81.6557),
    ("Fort Worth", 32.7555, -97.3308),
    ("Columbus", 39.9612, -82.9988),
    ("Charlotte", 35.2271, -80.8431),
    ("San Francisco", 37.7749, -122.4194),
    ("Indianapolis", 39.7684, -86.1581),
    ("Seattle", 47.6062, -122.3321),
    ("Denver", 39.7392, -104.9903),
    ("Boston", 42.3601, -71.0589),
    ("Washington DC", 38.9072, -77.0369),
    ("Nashville", 36.1627, -86.7816),
    ("Detroit", 42.3314, -83.0458),
    ("Portland", 45.5152, -122.6784),
    ("Las Vegas", 36.1699, -115.1398),
    ("Miami", 25.7617, -80.1918),
    ("Atlanta", 33.7490, -84.3880),
    ("Minneapolis", 44.9778, -93.2650),
    ("Cleveland", 41.4993, -81.6944),
    ("Tampa", 27.9506, -82.4572),
]

# Nearby/supporting US cities: same regions, help prediction via more training signal
NEARBY_US_CITIES = [
    ("Newark", 40.7357, -74.1724),       # NYC metro
    ("Jersey City", 40.7178, -74.0431),   # NYC metro
    ("Long Beach", 33.7701, -118.1937),  # LA metro
    ("Oakland", 37.8044, -122.2712),     # SF Bay Area
    ("Milwaukee", 43.0389, -87.9065),    # near Chicago
    ("Mesa", 33.4152, -112.8315),        # Phoenix metro
    ("Arlington TX", 32.7357, -97.1081), # Dallas–Fort Worth
    ("Baltimore", 39.2904, -76.6122),    # DC corridor
    ("St. Louis", 38.6270, -90.1994),
    ("Kansas City", 39.0997, -94.5786),
    ("New Orleans", 29.9511, -90.0715),
    ("Pittsburgh", 40.4406, -79.9959),
    ("Sacramento", 38.5816, -121.4944),
    ("Raleigh", 35.7796, -78.6382),      # near Charlotte
    ("Salt Lake City", 40.7608, -111.8910),
]

# All cities used for data collection (major + nearby)
CITIES = list(MAJOR_US_CITIES) + list(NEARBY_US_CITIES)

# Hourly variables to fetch (forecast and archive)
HOURLY_VARS = (
    "temperature_2m,relative_humidity_2m,precipitation,cloud_cover,"
    "wind_speed_10m,wind_direction_10m,pressure_msl"
)

# Daily variables for targets and features
DAILY_VARS = (
    "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
    "precipitation_sum,wind_speed_10m_max"
)

# Historical range for training (days back from today)
HISTORICAL_DAYS = 365

# Forecast horizon we care about (current day + next day)
FORECAST_DAYS = 2

# When collecting forecast data to disk, how many days ahead to fetch (max 16)
FORECAST_COLLECTION_DAYS = 16

# NWS CLI: max version links to scrape per station when collecting historical data (each version ≈ one day)
NWS_MAX_VERSIONS_HISTORICAL = 60

# Stations to use for gentle backfill (Kalshi-style major cities: https://kalshi.com/category/climate/daily-temperature)
# Subset of NWS_CLI_STATIONS; backfill script uses these plus long delays to avoid overloading the server
NWS_BACKFILL_STATIONS = [
    ("New York", "OKX", "NYC"),
    ("Los Angeles", "LOX", "LAX"),
    ("Chicago", "LOT", "ORD"),
    ("Houston", "HGX", "IAH"),
    ("Phoenix", "PSR", "PHX"),
    ("Philadelphia", "PHI", "PHL"),
    ("San Antonio", "EWX", "SAT"),
    ("San Diego", "SGX", "SAN"),
    ("Dallas", "FWD", "DFW"),
    ("Jacksonville", "JAX", "JAX"),
    ("San Francisco", "MTR", "SFO"),
    ("Columbus", "ILN", "CMH"),
    ("Charlotte", "GSP", "CLT"),
    ("Seattle", "SEW", "SEA"),
    ("Denver", "BOU", "DEN"),
    ("Boston", "BOX", "BOS"),
    ("Washington DC", "LWX", "DCA"),
    ("Nashville", "OHX", "BNA"),
    ("Detroit", "DTX", "DTW"),
    ("Portland", "PQR", "PDX"),
    ("Las Vegas", "VEF", "LAS"),
    ("Miami", "MFL", "MIA"),
    ("Atlanta", "FFC", "ATL"),
    ("Minneapolis", "MPX", "MSP"),
    ("Cleveland", "CLE", "CLE"),
    ("Tampa", "TBW", "TPA"),
]

# NWS CLI: max versions to request per station during backfill (each ≈ one day of history)
NWS_BACKFILL_MAX_VERSIONS = 60

# NWS CLI backfill: delay in seconds between each version request (per station)
NWS_BACKFILL_DELAY_VERSIONS = 2.0
# NWS CLI backfill: delay in seconds between finishing one station and starting the next
NWS_BACKFILL_DELAY_STATIONS = 12.0
# NWS CLI backfill: max random jitter (seconds) added to each delay
NWS_BACKFILL_JITTER = 2.0

# NWS Climate Report (CLI) stations for scraping
# (city_name, site, issuedby) — see https://forecast.weather.gov/product.php?site=...&product=CLI&issuedby=...
# site = WFO code, issuedby = station/climate site id
NWS_CLI_STATIONS = [
    ("Los Angeles", "LOX", "LAX"),
    ("San Diego", "SGX", "SAN"),
    ("San Francisco", "MTR", "SFO"),
    ("New York", "OKX", "NYC"),
    ("Chicago", "LOT", "ORD"),
    ("Phoenix", "PSR", "PHX"),
    ("Seattle", "SEW", "SEA"),
    ("Denver", "BOU", "DEN"),
    ("Boston", "BOX", "BOS"),
    ("Miami", "MFL", "MIA"),
    ("Dallas", "FWD", "DFW"),
    ("Houston", "HGX", "IAH"),
    ("Washington DC", "LWX", "DCA"),
    ("Philadelphia", "PHI", "PHL"),
    ("Atlanta", "FFC", "ATL"),
    ("Detroit", "DTX", "DTW"),
    ("Minneapolis", "MPX", "MSP"),
    ("Cleveland", "CLE", "CLE"),
    ("Portland", "PQR", "PDX"),
    ("Las Vegas", "VEF", "LAS"),
    ("Tampa", "TBW", "TPA"),
    ("San Antonio", "EWX", "SAT"),
    ("Charlotte", "GSP", "CLT"),
    ("Nashville", "OHX", "BNA"),
    ("Columbus", "ILN", "CMH"),
    ("Jacksonville", "JAX", "JAX"),
]

# Run loop (python main.py run): hours between full daily collections (forecast + NWS + gas)
# Default 12 = run twice per day. Override with --interval N.
RUN_LOOP_INTERVAL_HOURS = 12

# Treasury yield curve: start year for historical backfill (e.g. 2020 = fetch from 2020-01 to now)
TREASURY_BACKFILL_START_YEAR = 2020

# Treasury CSV base URL (month appended as /YYYYMM; query string added for type and format)
# If the site changes, update this. Example: ".../daily-treasury-rates.csv/all"
TREASURY_CSV_BASE = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/all"
