"""Read/write CSV files for hourly, daily, forecast, NWS, and gas data."""

from pathlib import Path

import pandas as pd


def save_data(hourly: pd.DataFrame, daily: pd.DataFrame, directory: str | Path = "data") -> None:
    """Save collected hourly and daily DataFrames to CSV."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    if not hourly.empty:
        hourly.to_csv(path / "hourly.csv", index=True)
    if not daily.empty:
        daily.to_csv(path / "daily.csv", index=True)


def save_forecast(hourly: pd.DataFrame, daily: pd.DataFrame, directory: str | Path = "data") -> None:
    """Save forecast hourly and daily DataFrames to CSV."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    if not hourly.empty:
        hourly.to_csv(path / "forecast_hourly.csv", index=True)
    if not daily.empty:
        daily.to_csv(path / "forecast_daily.csv", index=True)


def load_forecast(directory: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load forecast hourly and daily CSVs from directory."""
    path = Path(directory)
    hourly_path = path / "forecast_hourly.csv"
    daily_path = path / "forecast_daily.csv"
    hourly = (
        pd.read_csv(hourly_path, index_col=0, parse_dates=True)
        if hourly_path.exists()
        else pd.DataFrame()
    )
    daily = (
        pd.read_csv(daily_path, index_col=0, parse_dates=True)
        if daily_path.exists()
        else pd.DataFrame()
    )
    if not daily.empty:
        daily.index = pd.to_datetime(daily.index)
    return hourly, daily


def load_data(directory: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load hourly and daily CSVs from directory."""
    path = Path(directory)
    hourly_path = path / "hourly.csv"
    daily_path = path / "daily.csv"

    hourly = pd.read_csv(hourly_path, index_col=0, parse_dates=True) if hourly_path.exists() else pd.DataFrame()
    daily = pd.read_csv(daily_path, index_col=0, parse_dates=True) if daily_path.exists() else pd.DataFrame()
    if not daily.empty and daily.index.name == "date":
        daily.index = pd.to_datetime(daily.index)
    return hourly, daily


def save_gas_data(
    national_df: pd.DataFrame,
    state_df: pd.DataFrame,
    directory: str | Path = "data",
) -> None:
    """Save gas price DataFrames to data/gas_national.csv and data/gas_state.csv."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    if not national_df.empty:
        national_df.to_csv(path / "gas_national.csv", index=False)
    if not state_df.empty:
        state_df.to_csv(path / "gas_state.csv", index=False)


def load_gas_data(directory: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load gas price CSVs from directory. Returns (national_df, state_df)."""
    path = Path(directory)
    national = (
        pd.read_csv(path / "gas_national.csv")
        if (path / "gas_national.csv").exists()
        else pd.DataFrame()
    )
    state = (
        pd.read_csv(path / "gas_state.csv")
        if (path / "gas_state.csv").exists()
        else pd.DataFrame()
    )
    if not national.empty and "date" in national.columns:
        national["date"] = pd.to_datetime(national["date"]).dt.date
    if not state.empty and "date" in state.columns:
        state["date"] = pd.to_datetime(state["date"]).dt.date
    return national, state


def save_nws_data(df: pd.DataFrame, directory: str | Path = "data") -> Path:
    """Append or write scraped NWS data to data/nws_daily.csv. Uses report_date as date column."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    out_file = path / "nws_daily.csv"

    if df.empty:
        return out_file
    df = df.dropna(subset=["report_date"]).copy()
    if df.empty:
        return out_file

    if out_file.exists():
        try:
            existing = pd.read_csv(out_file)
            if "report_date" in existing.columns:
                existing["report_date"] = pd.to_datetime(existing["report_date"]).dt.date
            new_keys = set(zip(df["report_date"].astype(str), df["city"]))
            existing["_key"] = list(zip(existing["report_date"].astype(str), existing["city"]))
            existing = existing[~existing["_key"].isin(new_keys)].drop(columns=["_key"])
            df_combined = pd.concat([existing, df], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=["report_date", "city"], keep="last")
            df_combined = df_combined.sort_values(["report_date", "city"]).reset_index(drop=True)
        except Exception:
            df_combined = df
    else:
        df_combined = df

    df_combined.to_csv(out_file, index=False)
    return out_file


def load_nws_data(directory: str | Path = "data") -> pd.DataFrame:
    """Load NWS daily data from data/nws_daily.csv."""
    path = Path(directory) / "nws_daily.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "report_date" in df.columns:
        df["report_date"] = pd.to_datetime(df["report_date"]).dt.date
    return df


def save_treasury_data(df: pd.DataFrame, directory: str | Path = "data") -> Path:
    """Write treasury yield curve DataFrame to data/treasury_yield_curve.csv."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    out_file = path / "treasury_yield_curve.csv"
    if not df.empty:
        df.to_csv(out_file, index=False)
    return out_file


def load_treasury_data(directory: str | Path = "data") -> pd.DataFrame:
    """Load treasury yield curve from data/treasury_yield_curve.csv."""
    path = Path(directory) / "treasury_yield_curve.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    return df
