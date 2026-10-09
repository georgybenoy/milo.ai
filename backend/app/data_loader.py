"""
Load and validate orders.csv once at startup.
The DataFrame is held in memory — never reloaded per request.
"""

import logging
from pathlib import Path
from typing import Any
import pandas as pd

logger = logging.getLogger("milo.data_loader")

_df: pd.DataFrame | None = None

REQUIRED_COLUMNS: list[str] = [
    "order_id",
    "order_date",
    "customer_name",
    "city",
    "product",
    "category",
    "quantity",
    "unit_price_inr",
    "total_inr",
    "payment_method",
    "status",
]


class DatasetError(Exception):
    """Raised when the orders dataset fails integrity or schema validation."""
    pass


def load_orders(csv_path: str | Path, force_reload: bool = False) -> pd.DataFrame:
    """Load CSV, validate schema and data integrity, and return cleaned DataFrame.

    Raises DatasetError if any validation check fails.
    """
    global _df
    if _df is not None and not force_reload:
        return _df

    path = Path(csv_path)
    if not path.is_file():
        raise DatasetError(f"Dataset file does not exist or is not a file: {csv_path}")

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise DatasetError(f"Could not read CSV file: {exc}") from exc

    # Check 1: Dataset not empty
    if df.empty:
        raise DatasetError("Dataset is empty (0 rows).")

    # Check 2: All 11 required columns present
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise DatasetError(f"Missing required columns in CSV: {sorted(missing_cols)}")

    # Check 3: No missing or duplicate order_id
    if df["order_id"].isna().any() or (df["order_id"].astype(str).str.strip() == "").any():
        raise DatasetError("Dataset contains missing or empty order_id values.")

    dupes = df["order_id"].duplicated()
    if dupes.any():
        duplicate_ids = df.loc[dupes, "order_id"].tolist()
        raise DatasetError(f"Duplicate order IDs found: {duplicate_ids}")

    # Check 4: Dates parse to real date objects (no NaT)
    parsed_dates = pd.to_datetime(df["order_date"], errors="coerce")
    if parsed_dates.isna().any():
        bad_rows = df[parsed_dates.isna()]["order_id"].tolist()
        raise DatasetError(f"Invalid or unparseable order_date in rows: {bad_rows}")
    df["order_date"] = parsed_dates

    # Check 5: quantity, unit_price_inr, total_inr numeric and positive (> 0)
    for num_col in ["quantity", "unit_price_inr", "total_inr"]:
        numeric_series = pd.to_numeric(df[num_col], errors="coerce")
        if numeric_series.isna().any():
            bad_ids = df[numeric_series.isna()]["order_id"].tolist()
            raise DatasetError(f"Non-numeric values in column '{num_col}' for orders: {bad_ids}")
        if (numeric_series <= 0).any():
            bad_ids = df[numeric_series <= 0]["order_id"].tolist()
            raise DatasetError(f"Non-positive values in column '{num_col}' for orders: {bad_ids}")
        df[num_col] = numeric_series

    # Check 6: total_inr == quantity * unit_price_inr (tolerance: 0.01 for rounding)
    computed_total = df["quantity"] * df["unit_price_inr"]
    diff = (df["total_inr"] - computed_total).abs()
    mismatches = df[diff > 0.01]
    if not mismatches.empty:
        mismatch_ids = mismatches["order_id"].tolist()
        raise DatasetError(
            f"total_inr does not match quantity * unit_price_inr in orders: {mismatch_ids}"
        )

    # Check 7: No nulls in any other column
    if df[REQUIRED_COLUMNS].isna().any().any():
        raise DatasetError("Dataset contains null values in required columns.")

    # Normalised helper columns for filtering (preserve original display columns)
    df["_status"] = df["status"].astype(str).str.strip().str.casefold()
    df["_category"] = df["category"].astype(str).str.strip().str.casefold()
    df["_customer"] = df["customer_name"].astype(str).str.strip().str.casefold()
    df["_city"] = df["city"].astype(str).str.strip().str.casefold()
    df["_product"] = df["product"].astype(str).str.strip().str.casefold()
    df["_payment"] = df["payment_method"].astype(str).str.strip().str.casefold()

    _df = df
    return _df


def get_orders() -> pd.DataFrame:
    """Return the in-memory orders DataFrame. Raises DatasetError if not loaded."""
    if _df is None:
        raise DatasetError("Orders dataset not loaded or not ready. Call load_orders() first.")
    return _df


def reset_orders() -> None:
    """Reset the loaded orders DataFrame (primarily for testing)."""
    global _df
    _df = None


def get_dataset_metadata() -> dict[str, Any]:
    """Expose dataset metadata: record count, min/max order date."""
    df = get_orders()
    return {
        "record_count": int(len(df)),
        "min_order_date": df["order_date"].min().strftime("%Y-%m-%d"),
        "max_order_date": df["order_date"].max().strftime("%Y-%m-%d"),
    }
