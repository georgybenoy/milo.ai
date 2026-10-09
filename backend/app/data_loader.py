"""
Load and validate orders.csv once at startup.
The DataFrame is held in memory — never reloaded per request.
"""

import pandas as pd
from pathlib import Path

_df: pd.DataFrame | None = None


def load_orders(csv_path: Path) -> pd.DataFrame:
    """Load CSV, validate schema and data integrity, return cleaned DataFrame."""
    global _df
    if _df is not None:
        return _df

    df = pd.read_csv(csv_path, parse_dates=["order_date"])

    # --- Schema validation ---
    required_cols = {
        "order_id", "order_date", "customer_name", "city", "product",
        "category", "quantity", "unit_price_inr", "total_inr",
        "payment_method", "status",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in orders.csv: {missing}")

    # --- Data integrity checks ---
    # No nulls
    if df.isnull().any().any():
        raise ValueError("orders.csv contains null values")

    # No duplicate order IDs
    dupes = df["order_id"].duplicated()
    if dupes.any():
        raise ValueError(f"Duplicate order IDs: {df.loc[dupes, 'order_id'].tolist()}")

    # total_inr == quantity * unit_price_inr
    computed = df["quantity"] * df["unit_price_inr"]
    mismatches = df[df["total_inr"] != computed]
    if not mismatches.empty:
        raise ValueError(
            f"total_inr mismatch in rows: {mismatches['order_id'].tolist()}"
        )

    # Normalised columns for comparison (keep originals for display)
    df["_status"] = df["status"].str.strip().str.casefold()
    df["_category"] = df["category"].str.strip().str.casefold()
    df["_customer"] = df["customer_name"].str.strip().str.casefold()
    df["_city"] = df["city"].str.strip().str.casefold()
    df["_product"] = df["product"].str.strip().str.casefold()

    _df = df
    return _df


def get_orders() -> pd.DataFrame:
    """Return the already-loaded DataFrame. Raises if not loaded yet."""
    if _df is None:
        raise RuntimeError("Orders not loaded. Call load_orders() at startup.")
    return _df
