"""Tests for data loading and CSV validation."""

import pandas as pd


def test_csv_loads_60_rows(orders_df):
    assert len(orders_df) == 60


def test_csv_has_all_columns(orders_df):
    required = {
        "order_id", "order_date", "customer_name", "city", "product",
        "category", "quantity", "unit_price_inr", "total_inr",
        "payment_method", "status",
    }
    assert required.issubset(set(orders_df.columns))


def test_no_nulls(orders_df):
    # Exclude internal normalized columns
    public_cols = [c for c in orders_df.columns if not c.startswith("_")]
    assert not orders_df[public_cols].isnull().any().any()


def test_no_duplicate_ids(orders_df):
    assert not orders_df["order_id"].duplicated().any()


def test_totals_match(orders_df):
    """total_inr must equal quantity * unit_price_inr for every row."""
    computed = orders_df["quantity"] * orders_df["unit_price_inr"]
    assert (orders_df["total_inr"] == computed).all()


def test_date_range(orders_df):
    assert orders_df["order_date"].min() == pd.Timestamp("2026-06-01")
    assert orders_df["order_date"].max() == pd.Timestamp("2026-09-28")


def test_status_values(orders_df):
    expected = {"delivered", "cancelled", "returned", "processing", "shipped"}
    actual = set(orders_df["status"].unique())
    assert actual == expected


def test_category_values(orders_df):
    expected = {"Electronics", "Accessories", "Stationery", "Furniture"}
    actual = set(orders_df["category"].unique())
    assert actual == expected


def test_sanity_ord_1025(orders_df):
    """Cross-check: ORD-1025 → Karthik Rao, Kochi, Wireless Mouse ×3, ₹2,397, delivered, 2026-07-14."""
    row = orders_df[orders_df["order_id"] == "ORD-1025"].iloc[0]
    assert row["customer_name"] == "Karthik Rao"
    assert row["city"] == "Kochi"
    assert row["product"] == "Wireless Mouse"
    assert row["quantity"] == 3
    assert row["total_inr"] == 2397
    assert row["status"] == "delivered"
    assert row["order_date"] == pd.Timestamp("2026-07-14")
