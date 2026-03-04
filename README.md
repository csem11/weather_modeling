# Weather & related data collection

A **data collection** toolkit for weather (Open-Meteo, NWS) and gas prices (AAA). It fetches, stores, and builds consolidated datasets under a single `data/` directory. No API keys required for the default sources.

---

## Goal

Collect and persist:

- **Weather**: historical and forecast data (hourly/daily) from Open-Meteo; observed daily climate (max/min temp, precip) from NWS for US stations.
- **Gas prices**: national and state-level AAA gas prices.

Dataset construction (e.g. merging sources, building feature tables with lags and NWS targets) is supported in code so the same data can later be used for modeling or analysis. **Model training and prediction are out of scope for this repo**; the focus is ingestion and dataset building.

---

## Current status

| Area              | Status | Notes |
|-------------------|--------|--------|
| Open-Meteo        | ✅     | Historical (archive) + forecast; hourly/daily; configurable cities. |
| NWS climate (CLI) | ✅     | Scrape daily reports; optional historical backfill via version links. |
| AAA gas prices    | ✅     | National + state table + per-state detail; optional run loop. |
| Dataset building  | ✅     | `data_collector`: build feature tables, merge NWS targets (temps in °F). |
| Modeling          | ❌     | Not included; use this repo for data only. |

---

## Setup

```bash
git clone <repo-url>
cd weather_modeling
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

## Usage

### Open-Meteo forecast

Fetch and save forecast (and optional past days) to `data/forecast_hourly.csv` and `data/forecast_daily.csv`:

```bash
python main.py collect
# or
python collect_forecast.py
```

Configure cities and how many days in `config.py` (`CITIES`, `FORECAST_COLLECTION_DAYS`).

### NWS climate reports (CLI)

Scrape [NWS daily climate reports](https://forecast.weather.gov/product.php?site=LOX&product=CLI&issuedby=LAX) into `data/nws_daily.csv` (one row per station per report date; max/min temp °F, precip, etc.):

```bash
python main.py nws                    # Latest report per station
python main.py nws --historical      # Follow version links for more history
# or
python collect_nws.py [--historical]
```

Stations: `config.NWS_CLI_STATIONS`. For a gentle historical backfill (e.g. Kalshi-style major cities):

```bash
python backfill_nws.py               # Uses long delays between requests
python backfill_nws.py --dry-run
python backfill_nws.py --max-versions 30
```

### AAA gas prices

Append national and state gas prices to `data/gas_national.csv` and `data/gas_state.csv`:

```bash
python fetch_gas_prices.py
python fetch_gas_prices.py --data-dir data
```

Optional: run a loop that periodically checks for today’s gas data and fetches if missing:

```bash
python main.py run
python main.py run --interval 6 --data-dir data
```

---

## Data layout

| File(s)              | Filled by              | Description |
|----------------------|------------------------|-------------|
| `data/hourly.csv`    | (manual/script)        | Open-Meteo historical hourly; used with archive API. |
| `data/daily.csv`     | (manual/script)        | Open-Meteo historical daily. |
| `data/forecast_hourly.csv` | `main.py collect` | Open-Meteo forecast hourly. |
| `data/forecast_daily.csv`  | `main.py collect` | Open-Meteo forecast daily. |
| `data/nws_daily.csv` | `main.py nws` / `backfill_nws.py` | NWS CLI: report_date, city, site, issuedby, max/min temp (°F), precip, etc. |
| `data/gas_national.csv` | `fetch_gas_prices.py` | National averages by fuel and time period. |
| `data/gas_state.csv` | `fetch_gas_prices.py`  | One row per date per state (regular, mid_grade, premium, diesel). |

Historical Open-Meteo (hourly/daily) is not fetched by a single built-in command; use the archive API and `data_collector` helpers (e.g. `collect_historical`, `save_data`) from your own script or notebook if needed.

---

## Dataset construction

`data_collector.py` provides:

- **`build_training_data(daily_df, hourly_df)`** – Builds a feature table (lags, hourly aggregates, calendar) from Open-Meteo daily/hourly; all temperatures in °F.
- **`add_nws_targets(df, nws_df)`** – Merges next-day high/low targets from NWS (by city and date+1); temps in °F.
- **`load_data`**, **`load_forecast`**, **`load_gas_data`** – Load saved CSVs. NWS: **`nws_scraper.load_nws_data()`**.

Example (after you have `daily`, `hourly`, and NWS data):

```python
from data_collector import build_training_data, add_nws_targets, load_data
from nws_scraper import load_nws_data

hourly, daily = load_data("data")
nws_df = load_nws_data("data")
df = build_training_data(daily, hourly)
df = add_nws_targets(df, nws_df)
# df has features + target_next_day_high, target_next_day_low (°F)
```

---

## Configuration

- **`config.py`**: Open-Meteo URLs; city lists (e.g. `CITIES`, `NWS_CLI_STATIONS`, `NWS_BACKFILL_STATIONS`); forecast/history lengths; NWS backfill delays; gas-check interval for `main.py run`.
- No API keys for Open-Meteo (non-commercial) or NWS. AAA is public scraping.

---

## License

Use and adapt as you like. Respect each data provider’s terms (Open-Meteo, NWS, AAA) when using or redistributing data.
