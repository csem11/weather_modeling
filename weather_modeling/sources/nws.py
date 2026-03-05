"""
Scrape NWS Climate (CLI) reports from forecast.weather.gov and parse into structured data.

Reports: https://forecast.weather.gov/product.php?site=LOX&product=CLI&issuedby=LAX
Each report is the daily climatological summary for one station (yesterday's obs).
Use version=N in the URL to fetch older issuances (historical data).
"""

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

from weather_modeling.config import NWS_CLI_STATIONS
from weather_modeling.storage.io import load_nws_data as _load_nws_data
from weather_modeling.storage.io import save_nws_data as _save_nws_data

NWS_PRODUCT_BASE = "https://forecast.weather.gov/product.php"
USER_AGENT = "WeatherModeling/1.0 (educational; contact optional)"
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.4

MONTH_NAMES = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def _f_to_c(f: float) -> float:
    return (f - 32) * 5 / 9


def _get_report_text(site: str, issuedby: str, version: int | None = None) -> str | None:
    """Fetch CLI product page and return the main text content (pre or body)."""
    params = {"site": site, "product": "CLI", "issuedby": issuedby}
    if version is not None:
        params["version"] = version
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(NWS_PRODUCT_BASE, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
    except requests.RequestException:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    pre = soup.find("pre")
    if pre:
        return pre.get_text(separator="\n")
    for tag in soup.find_all(class_=re.compile(r"pre|product", re.I)):
        if tag.get_text().strip().startswith("CLIMATE"):
            return tag.get_text(separator="\n")
    return None


def _get_version_links(site: str, issuedby: str) -> list[int]:
    """Fetch the product index page and parse version links (1, 2, 3, ...) for historical issuances."""
    params = {"site": site, "product": "CLI", "issuedby": issuedby}
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(NWS_PRODUCT_BASE, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
    except requests.RequestException:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    versions = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        match = re.search(r"version=(\d+)", href, re.IGNORECASE)
        if match:
            v = int(match.group(1))
            if v not in versions:
                versions.append(v)
    return sorted(versions, reverse=True)


def _parse_cli_report(text: str, city: str, site: str, issuedby: str) -> dict[str, Any] | None:
    """Parse CLI report text. Returns one row: date, city, site, issuedby, max_temp_f, min_temp_f, etc."""
    if not text or "CLIMATE" not in text.upper():
        return None
    out = {"city": city, "site": site, "issuedby": issuedby}

    date_m = re.search(
        r"CLIMATE\s+SUMMARY\s+FOR\s+(\w+)\s+(\d+)\s+(\d{4})",
        text,
        re.IGNORECASE,
    )
    if date_m:
        month_name, day, year = date_m.group(1).upper()[:3], int(date_m.group(2)), int(date_m.group(3))
        month = MONTH_NAMES.get(month_name)
        if month:
            out["report_date"] = datetime(year, month, day).date()
            out["report_date_parsed"] = out["report_date"].isoformat()
    else:
        out["report_date"] = None
        out["report_date_parsed"] = None

    max_m = re.search(r"MAXIMUM\s+(\d+)\s+(?:\d|\.|:|\w)", text)
    min_m = re.search(r"MINIMUM\s+(\d+)\s+(?:\d|\.|:|\w)", text)
    if max_m:
        out["max_temp_f"] = float(max_m.group(1))
        out["max_temp_c"] = round(_f_to_c(out["max_temp_f"]), 2)
    else:
        out["max_temp_f"] = None
        out["max_temp_c"] = None
    if min_m:
        out["min_temp_f"] = float(min_m.group(1))
        out["min_temp_c"] = round(_f_to_c(out["min_temp_f"]), 2)
    else:
        out["min_temp_f"] = None
        out["min_temp_c"] = None

    precip_section = re.search(r"PRECIPITATION\s*\(IN\)(.*?)(?=SNOWFALL|DEGREE|WIND|$)", text, re.DOTALL | re.IGNORECASE)
    if precip_section:
        block = precip_section.group(1)
        precip_m = re.search(r"YESTERDAY\s+(\d+\.?\d*)", block)
        if precip_m:
            try:
                out["precip_in"] = float(precip_m.group(1))
            except ValueError:
                out["precip_in"] = None
        else:
            out["precip_in"] = None
    else:
        out["precip_in"] = None

    out["source"] = "nws_cli"
    return out


def scrape_one(city: str, site: str, issuedby: str, version: int | None = None) -> dict[str, Any] | None:
    """Fetch and parse one CLI report. Returns parsed row or None on failure."""
    text = _get_report_text(site, issuedby, version=version)
    if not text:
        return None
    return _parse_cli_report(text, city, site, issuedby)


def scrape_one_versions(
    city: str,
    site: str,
    issuedby: str,
    max_versions: int = 60,
    stop_after_empty: int = 3,
    delay_seconds: float | None = None,
    *,
    progress_interval: int | None = None,
) -> list[dict[str, Any]]:
    """Fetch multiple versioned reports for one station (latest + historical). Returns list of parsed rows.
    If progress_interval is set (e.g. 10), prints a dot every that many version requests to show activity.
    """
    delay = delay_seconds if delay_seconds is not None else REQUEST_DELAY
    versions = _get_version_links(site, issuedby)
    if not versions:
        versions = list(range(1, max_versions + 1))
    else:
        versions = [v for v in versions if 1 <= v <= max_versions][:max_versions]
    rows = []
    seen_dates = set()
    empty_streak = 0
    for vi, v in enumerate(versions):
        if progress_interval and vi > 0 and vi % progress_interval == 0:
            print(".", end="", flush=True)
        row = scrape_one(city, site, issuedby, version=v)
        time.sleep(delay)
        if not row or not row.get("report_date"):
            empty_streak += 1
            if empty_streak >= stop_after_empty:
                break
            continue
        empty_streak = 0
        rd = row["report_date"]
        if rd in seen_dates:
            continue
        seen_dates.add(rd)
        rows.append(row)
    return rows


def scrape_all(stations: list[tuple[str, str, str]] | None = None) -> pd.DataFrame:
    """Scrape all configured NWS CLI stations. Returns DataFrame with one row per station (latest report)."""
    stations = stations or NWS_CLI_STATIONS
    rows = []
    for city, site, issuedby in stations:
        row = scrape_one(city, site, issuedby)
        if row:
            rows.append(row)
        time.sleep(REQUEST_DELAY)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def scrape_all_historical(
    stations: list[tuple[str, str, str]] | None = None,
    max_versions_per_station: int = 60,
    *,
    verbose: bool = True,
) -> pd.DataFrame:
    """Scrape latest + historical CLI reports for each station via version links."""
    stations = stations or NWS_CLI_STATIONS
    all_rows = []
    n = len(stations)
    for i, (city, site, issuedby) in enumerate(stations):
        if verbose:
            print(f"  [{i + 1}/{n}] {city} ({site}/{issuedby}) ... ", end="", flush=True)
        station_rows = scrape_one_versions(
            city, site, issuedby,
            max_versions=max_versions_per_station,
            progress_interval=10 if verbose else None,
        )
        all_rows.extend(station_rows)
        if verbose:
            print(f" {len(station_rows)} rows", flush=True)
    if not all_rows:
        return pd.DataFrame()
    return pd.DataFrame(all_rows)


def save_nws_data(df: pd.DataFrame, directory: str | Path = "data") -> Path:
    """Append or write scraped NWS data to data/nws_daily.csv. Delegates to storage."""
    return _save_nws_data(df, directory)


def load_nws_data(directory: str | Path = "data") -> pd.DataFrame:
    """Load NWS daily data from data/nws_daily.csv. Delegates to storage."""
    return _load_nws_data(directory)
