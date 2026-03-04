"""Fetch AAA gas prices (national + state) and build/save to project data storage."""

from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from weather_modeling.storage.io import save_gas_data

REQUEST_DELAY_STATE = 0.5

US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL",
    "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
    "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
    "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI",
    "WY",
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _parse_price(text: str) -> float | None:
    """Extract a float price from text like '$3.109' or '3.109'."""
    text = text.strip().replace("$", "").replace(",", "")
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def _scrape_national_averages(session: requests.Session) -> dict:
    """Scrape national average gas prices from the AAA homepage."""
    url = "https://gasprices.aaa.com/"
    resp = session.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text

    fuel_types = ["regular", "mid_grade", "premium", "diesel", "e85"]
    time_period_labels = [
        ("current", "Current"),
        ("yesterday", "Yesterday"),
        ("week_ago", "Week Ago"),
        ("month_ago", "Month Ago"),
        ("year_ago", "Year Ago"),
    ]

    result: dict = {}
    date_match = re.search(r"Price as of\s+(\d{1,2}/\d{1,2}/\d{2,4})", html)
    if date_match:
        result["price_date"] = date_match.group(1)

    table_match = re.search(
        r'<table[^>]*class="table-mob"[^>]*>(.*?)</table>', html, re.DOTALL
    )
    if not table_match:
        return result

    table_html = table_match.group(1)
    row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
    cell_pattern = re.compile(r"<td[^>]*>\s*(.*?)\s*</td>", re.DOTALL)

    for ft in fuel_types:
        result[ft] = {}

    for row_match in row_pattern.finditer(table_html):
        row_html = row_match.group(1)
        cells = cell_pattern.findall(row_html)
        if not cells:
            continue
        label = re.sub(r"<[^>]+>", "", cells[0]).strip()
        period_key = None
        for key, search_text in time_period_labels:
            if search_text.lower() in label.lower():
                period_key = key
                break
        if period_key is None:
            continue
        price_cells = cells[1:]
        for i, ft in enumerate(fuel_types):
            if i < len(price_cells):
                price = _parse_price(re.sub(r"<[^>]+>", "", price_cells[i]))
                result[ft][period_key] = price

    return result


def _scrape_state_table(session: requests.Session) -> list[dict]:
    """Scrape all-states table from AAA state averages page."""
    url = "https://gasprices.aaa.com/state-gas-price-averages/"
    resp = session.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text

    states = []
    row_pattern = re.compile(
        r"<tr[^>]*>\s*"
        r"<td[^>]*>\s*(.*?)\s*</td>\s*"
        r"<td[^>]*>\s*(.*?)\s*</td>\s*"
        r"<td[^>]*>\s*(.*?)\s*</td>\s*"
        r"<td[^>]*>\s*(.*?)\s*</td>\s*"
        r"<td[^>]*>\s*(.*?)\s*</td>\s*"
        r"</tr>",
        re.DOTALL | re.IGNORECASE,
    )

    for match in row_pattern.finditer(html):
        state_name = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        if not state_name or state_name.lower() in ("state", ""):
            continue
        regular = _parse_price(re.sub(r"<[^>]+>", "", match.group(2)))
        mid_grade = _parse_price(re.sub(r"<[^>]+>", "", match.group(3)))
        premium = _parse_price(re.sub(r"<[^>]+>", "", match.group(4)))
        diesel = _parse_price(re.sub(r"<[^>]+>", "", match.group(5)))
        if regular is not None:
            states.append({
                "state": state_name,
                "regular": regular,
                "mid_grade": mid_grade,
                "premium": premium,
                "diesel": diesel,
            })
    return states


def _scrape_state_detail(session: requests.Session, state_abbr: str) -> dict:
    """Scrape detailed gas prices for a specific state (time-period comparisons)."""
    url = f"https://gasprices.aaa.com/?state={state_abbr}"
    resp = session.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text

    fuel_types = ["regular", "mid_grade", "premium", "diesel"]
    time_period_labels = [
        ("current", "Current"),
        ("yesterday", "Yesterday"),
        ("week_ago", "Week Ago"),
        ("month_ago", "Month Ago"),
        ("year_ago", "Year Ago"),
    ]

    result: dict = {"state": state_abbr}
    table_match = re.search(
        r'<table[^>]*class="table-mob"[^>]*>(.*?)</table>', html, re.DOTALL
    )
    if not table_match:
        return result

    table_html = table_match.group(1)
    row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
    cell_pattern = re.compile(r"<td[^>]*>\s*(.*?)\s*</td>", re.DOTALL)

    for ft in fuel_types:
        result[ft] = {}

    for row_match in row_pattern.finditer(table_html):
        row_html = row_match.group(1)
        cells = cell_pattern.findall(row_html)
        if not cells:
            continue
        label = re.sub(r"<[^>]+>", "", cells[0]).strip()
        period_key = None
        for key, search_text in time_period_labels:
            if search_text.lower() in label.lower():
                period_key = key
                break
        if period_key is None:
            continue
        price_cells = cells[1:]
        for i, ft in enumerate(fuel_types):
            if i < len(price_cells):
                price = _parse_price(re.sub(r"<[^>]+>", "", price_cells[i]))
                result[ft][period_key] = price
    return result


def fetch_all_gas_prices() -> dict:
    """Fetch national averages and all state prices. Returns combined dict."""
    session = requests.Session()
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"Fetching AAA gas prices for {today}...")
    print("  Fetching national averages...")
    national = _scrape_national_averages(session)

    print("  Fetching state averages table...")
    state_table = _scrape_state_table(session)

    print(f"  Fetching detail pages for {len(US_STATES)} states...")
    state_details = {}
    for i, state_abbr in enumerate(US_STATES):
        try:
            detail = _scrape_state_detail(session, state_abbr)
            state_details[state_abbr] = detail
            if (i + 1) % 10 == 0:
                print(f"    ... {i + 1}/{len(US_STATES)} states done")
            time.sleep(REQUEST_DELAY_STATE)
        except Exception as e:
            print(f"    Warning: failed to fetch {state_abbr}: {e}")
            state_details[state_abbr] = {"state": state_abbr, "error": str(e)}

    return {
        "date": today,
        "fetch_timestamp": datetime.now().isoformat(),
        "national": national,
        "state_table": state_table,
        "state_details": state_details,
    }


def _build_national_df(data: dict) -> pd.DataFrame:
    """Build one row for national averages (flattened columns)."""
    row = {
        "date": data["date"],
        "fetch_timestamp": data["fetch_timestamp"],
        "price_date": data.get("national", {}).get("price_date"),
    }
    for fuel in ["regular", "mid_grade", "premium", "diesel", "e85"]:
        prices = data.get("national", {}).get(fuel) or {}
        for period in ["current", "yesterday", "week_ago", "month_ago", "year_ago"]:
            key = f"{fuel}_{period}"
            row[key] = prices.get(period)
    return pd.DataFrame([row])


def _build_state_df(data: dict) -> pd.DataFrame:
    """Build one row per state from state_table (current snapshot)."""
    rows = []
    for st in data.get("state_table", []):
        rows.append({
            "date": data["date"],
            "fetch_timestamp": data["fetch_timestamp"],
            "state": st["state"],
            "regular": st.get("regular"),
            "mid_grade": st.get("mid_grade"),
            "premium": st.get("premium"),
            "diesel": st.get("diesel"),
        })
    return pd.DataFrame(rows)


def save_gas_to_data(
    data: dict,
    directory: Path | str,
) -> tuple[Path, Path]:
    """
    Append today's gas data to data/gas_national.csv and data/gas_state.csv.
    Dedupes by date (and state for state file). Returns (national_path, state_path).
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    national_new = _build_national_df(data)
    state_new = _build_state_df(data)

    national_path = directory / "gas_national.csv"
    state_path = directory / "gas_state.csv"

    if national_path.exists():
        national_existing = pd.read_csv(national_path)
        national_existing["date"] = pd.to_datetime(national_existing["date"]).dt.date
        new_dates = set(national_new["date"].astype(str))
        national_existing = national_existing[~national_existing["date"].astype(str).isin(new_dates)]
        national_df = pd.concat([national_existing, national_new], ignore_index=True)
        national_df = national_df.drop_duplicates(subset=["date"], keep="last").sort_values("date").reset_index(drop=True)
    else:
        national_df = national_new

    if state_path.exists():
        state_existing = pd.read_csv(state_path)
        state_existing["date"] = pd.to_datetime(state_existing["date"]).dt.date
        new_keys = set(zip(state_new["date"].astype(str), state_new["state"]))
        state_existing["_key"] = list(zip(state_existing["date"].astype(str), state_existing["state"]))
        state_existing = state_existing[~state_existing["_key"].isin(new_keys)].drop(columns=["_key"])
        state_df = pd.concat([state_existing, state_new], ignore_index=True)
        state_df = state_df.drop_duplicates(subset=["date", "state"], keep="last").sort_values(["date", "state"]).reset_index(drop=True)
    else:
        state_df = state_new

    save_gas_data(national_df, state_df, directory)
    return national_path, state_path
