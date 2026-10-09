"""Tests for data loading, schema validation, and CSV integrity."""

from pathlib import Path
import pytest
import pandas as pd

from app.data_loader import (
    load_orders,
    get_orders,
    get_dataset_metadata,
    reset_orders,
    DatasetError,
    REQUIRED_COLUMNS,
)
from app.config import CSV_PATH


@pytest.fixture(autouse=True)
def ensure_clean_orders():
    """Ensure orders are properly loaded for each test, resetting after temp tests."""
    reset_orders()
    load_orders(CSV_PATH, force_reload=True)
    yield
    reset_orders()
    load_orders(CSV_PATH, force_reload=True)


def test_csv_loads_60_rows():
    df = get_orders()
    assert len(df) == 60


def test_csv_has_all_required_columns():
    df = get_orders()
    assert set(REQUIRED_COLUMNS).issubset(set(df.columns))


def test_no_nulls_in_required_columns():
    df = get_orders()
    assert not df[REQUIRED_COLUMNS].isnull().any().any()


def test_no_duplicate_ids():
    df = get_orders()
    assert not df["order_id"].duplicated().any()


def test_totals_match():
    """total_inr must equal quantity * unit_price_inr for every row."""
    df = get_orders()
    computed = df["quantity"] * df["unit_price_inr"]
    diff = (df["total_inr"] - computed).abs()
    assert (diff <= 0.01).all()


def test_date_range():
    df = get_orders()
    assert df["order_date"].min() == pd.Timestamp("2026-06-01")
    assert df["order_date"].max() == pd.Timestamp("2026-09-28")


def test_status_values():
    df = get_orders()
    expected = {"delivered", "cancelled", "returned", "processing", "shipped"}
    assert set(df["status"].unique()) == expected


def test_category_values():
    df = get_orders()
    expected = {"Electronics", "Accessories", "Stationery", "Furniture"}
    assert set(df["category"].unique()) == expected


def test_sanity_ord_1025():
    """Cross-check §0.3: ORD-1025 → Karthik Rao, Kochi, Wireless Mouse ×3, ₹2,397, delivered, 2026-07-14."""
    df = get_orders()
    row = df[df["order_id"] == "ORD-1025"].iloc[0]
    assert row["customer_name"] == "Karthik Rao"
    assert row["city"] == "Kochi"
    assert row["product"] == "Wireless Mouse"
    assert row["quantity"] == 3
    assert row["total_inr"] == 2397
    assert row["status"] == "delivered"
    assert row["order_date"] == pd.Timestamp("2026-07-14")


def test_dataset_metadata():
    """Verify get_dataset_metadata exposed for sidebar."""
    meta = get_dataset_metadata()
    assert meta["record_count"] == 60
    assert meta["min_order_date"] == "2026-06-01"
    assert meta["max_order_date"] == "2026-09-28"


def test_normalised_helper_columns():
    """Verify helper columns are lowercase and do not mutate displayed columns."""
    df = get_orders()
    assert "_status" in df.columns
    assert "_category" in df.columns
    assert "_customer" in df.columns
    assert "_city" in df.columns
    assert "_product" in df.columns
    assert "_payment" in df.columns

    # Original columns preserved exactly
    row = df[df["order_id"] == "ORD-1025"].iloc[0]
    assert row["status"] == "delivered"
    assert row["_status"] == "delivered"
    assert row["category"] == "Electronics"
    assert row["_category"] == "electronics"


# ──────────────────────────── Validation Failure Fixtures ────────────────────────────


def test_validation_missing_file(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist.csv"
    with pytest.raises(DatasetError, match="does not exist"):
        load_orders(non_existent, force_reload=True)


def test_validation_empty_dataset(tmp_path: Path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("order_id,order_date\n", encoding="utf-8")
    with pytest.raises(DatasetError, match="empty"):
        load_orders(empty_csv, force_reload=True)


def test_validation_missing_column(tmp_path: Path):
    bad_csv = tmp_path / "missing_col.csv"
    # Omit 'payment_method'
    cols = [c for c in REQUIRED_COLUMNS if c != "payment_method"]
    bad_csv.write_text(",".join(cols) + "\n" + "ORD-1001,2026-06-01,Alice,Pune,Pen,Stationery,1,50,50,delivered\n", encoding="utf-8")
    with pytest.raises(DatasetError, match="Missing required columns"):
        load_orders(bad_csv, force_reload=True)


def test_validation_duplicate_ids(tmp_path: Path):
    bad_csv = tmp_path / "duplicate_id.csv"
    df = pd.read_csv(CSV_PATH).head(3).copy()
    df.loc[1, "order_id"] = df.loc[0, "order_id"]
    df.to_csv(bad_csv, index=False)
    with pytest.raises(DatasetError, match="Duplicate order IDs"):
        load_orders(bad_csv, force_reload=True)


def test_validation_bad_numeric_negative(tmp_path: Path):
    bad_csv = tmp_path / "negative_qty.csv"
    df = pd.read_csv(CSV_PATH).head(3).copy()
    df.loc[0, "quantity"] = -1
    df.to_csv(bad_csv, index=False)
    with pytest.raises(DatasetError, match="Non-positive values in column 'quantity'"):
        load_orders(bad_csv, force_reload=True)


def test_validation_bad_numeric_string(tmp_path: Path):
    bad_csv = tmp_path / "bad_numeric.csv"
    df = pd.read_csv(CSV_PATH).head(3).copy()
    df.loc[0, "total_inr"] = "one_hundred"
    df.to_csv(bad_csv, index=False)
    with pytest.raises(DatasetError, match="Non-numeric values in column 'total_inr'"):
        load_orders(bad_csv, force_reload=True)


def test_validation_total_mismatch(tmp_path: Path):
    bad_csv = tmp_path / "mismatch.csv"
    df = pd.read_csv(CSV_PATH).head(3).copy()
    df.loc[0, "total_inr"] = 99999
    df.to_csv(bad_csv, index=False)
    with pytest.raises(DatasetError, match="total_inr does not match"):
        load_orders(bad_csv, force_reload=True)


def test_validation_invalid_date(tmp_path: Path):
    bad_csv = tmp_path / "invalid_date.csv"
    df = pd.read_csv(CSV_PATH).head(3).copy()
    df.loc[0, "order_date"] = "not-a-real-date"
    df.to_csv(bad_csv, index=False)
    with pytest.raises(DatasetError, match="Invalid or unparseable order_date"):
        load_orders(bad_csv, force_reload=True)
