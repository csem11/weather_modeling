# Weather & related data collection

A **data collection** toolkit for weather (Open-Meteo, NWS) and gas prices (AAA). It fetches, stores, and builds consolidated datasets under a single `data/` directory. No API keys required for the default sources.

---

## Goal

Collect and persist:

- **Weather**: historical and forecast data (hourly/daily) from Open-Meteo; observed daily climate (max/min temp, precip) from NWS for US stations.
- **Gas prices**: national and state-level AAA gas prices.
- **Treasury yields**: daily Treasury yield curve (CMT rates by maturity) from U.S. Treasury CSV.

Dataset construction (e.g. merging sources, building feature tables with lags and NWS targets) is supported in code so the same data can later be used for modeling or analysis. **Model training and prediction are out of scope for this repo**; the focus is ingestion and dataset building.

---

## Current status

| Area              | Status | Notes |
|-------------------|--------|--------|
| Open-Meteo        | ✅     | Historical (archive) + forecast; hourly/daily; configurable cities. |
| NWS climate (CLI) | ✅     | Scrape daily reports; optional historical backfill via version links. |
| AAA gas prices    | ✅     | National + state table + per-state detail; optional run loop. |
| Treasury yield curve | ✅   | Daily CMT rates (CSV by month); optional backfill from start year. |
| Dataset building  | ✅     | `weather_modeling.pipeline`: build feature tables, merge NWS targets (temps in °F). |
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

Configure cities and how many days in `weather_modeling.config` (or root `config.py`) — `CITIES`, `FORECAST_COLLECTION_DAYS`.

### NWS climate reports (CLI)

Scrape [NWS daily climate reports](https://forecast.weather.gov/product.php?site=LOX&product=CLI&issuedby=LAX) into `data/nws_daily.csv` (one row per station per report date; max/min temp °F, precip, etc.):

```bash
python main.py nws                    # Latest report per station
python main.py nws --historical      # Follow version links for more history
# or
python collect_nws.py [--historical]
```

Stations: `weather_modeling.config.NWS_CLI_STATIONS`. For a gentle historical backfill (e.g. Kalshi-style major cities):

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

Optional: run indefinitely and perform full daily collection (forecast + NWS + gas) every 12 hours (twice per day):

```bash
python main.py run
python main.py run --interval 6 --data-dir data   # every 6 hours
```

### Treasury yield curve

Daily U.S. Treasury yield curve (CMT rates by maturity) from [home.treasury.gov](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve). Saved to `data/treasury_yield_curve.csv`:

```bash
python main.py treasury                    # Latest (current + previous month)
python main.py treasury --backfill        # Historical from config start year (default 2020)
python main.py treasury --backfill --start-year 2015
# or
python collect_treasury.py [--backfill] [--start-year YYYY]
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
| `data/treasury_yield_curve.csv` | `main.py treasury` | Daily Treasury yield curve (date + CMT rates by maturity). |

Historical Open-Meteo (hourly/daily) is not fetched by a single built-in command; use `weather_modeling.sources.open_meteo.collect_historical` and `weather_modeling.storage.save_data` from your own script or notebook if needed.

---

## Dataset construction

The `weather_modeling` package is organized as:

- **`weather_modeling.pipeline`** – **`build_training_data(daily_df, hourly_df)`** (feature table: lags, hourly aggregates, calendar; temps in °F); **`add_nws_targets(df, nws_df)`** (next-day high/low from NWS).
- **`weather_modeling.storage`** – **`load_data`**, **`load_forecast`**, **`load_gas_data`**, **`load_nws_data`**, **`load_treasury_data`** (and corresponding `save_*`).

Example (after you have `daily`, `hourly`, and NWS data):

```python
from weather_modeling.pipeline import build_training_data, add_nws_targets
from weather_modeling.storage import load_data, load_nws_data

hourly, daily = load_data("data")
nws_df = load_nws_data("data")
df = build_training_data(daily, hourly)
df = add_nws_targets(df, nws_df)
# df has features + target_next_day_high, target_next_day_low (°F)
```

---

## Configuration

- **`weather_modeling.config`** (and root **`config.py`** re-export): Open-Meteo URLs; city lists; forecast/history lengths; NWS backfill delays; `RUN_LOOP_INTERVAL_HOURS` for `main.py run` (default 12).
- No API keys for Open-Meteo (non-commercial) or NWS. AAA is public scraping.

## Project layout

- **`weather_modeling/`** – Main package:
  - **`config.py`** – API URLs, city lists, backfill/run-loop settings.
  - **`sources/`** – Data acquisition: `open_meteo`, `nws`, `gas`.
  - **`storage/`** – Load/save CSVs (hourly, daily, forecast, NWS, gas).
  - **`pipeline/`** – Dataset building: `build_training_data`, `add_nws_targets`, `merge_nws_into_daily`.
  - **`cli/`** – Entrypoints for `main.py collect | nws | run`.
- Root scripts **`main.py`**, **`collect_forecast.py`**, **`collect_nws.py`**, **`run_loop.py`**, **`backfill_nws.py`**, **`fetch_gas_prices.py`** – Thin wrappers that call the package.

---

## License

Use and adapt as you like. Respect each data provider’s terms (Open-Meteo, NWS, AAA) when using or redistributing data.
