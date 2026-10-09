"""Tests for deterministic tool functions (lookup_order and analyze_orders)."""

import pandas as pd
import pytest

from app.tools import lookup_order, analyze_orders, dispatch_tool, _format_inr
from app.data_loader import load_orders
from app.config import CSV_PATH


@pytest.fixture(scope="module", autouse=True)
def init_dataset():
    load_orders(CSV_PATH)


@pytest.fixture(scope="module")
def raw_df():
    df = pd.read_csv(CSV_PATH, parse_dates=["order_date"])
    df["_status"] = df["status"].str.strip().str.casefold()
    df["_category"] = df["category"].str.strip().str.casefold()
    df["_customer"] = df["customer_name"].str.strip().str.casefold()
    return df


# ──────────────────────────── Formatting Tests ────────────────────────────


class TestFormatINR:
    def test_small_number(self):
        assert _format_inr(250) == "₹250"

    def test_four_digits(self):
        assert _format_inr(2397) == "₹2,397"

    def test_six_digits(self):
        assert _format_inr(112282) == "₹1,12,282"

    def test_large_number(self):
        assert _format_inr(12345678) == "₹1,23,45,678"


# ──────────────────────────── lookup_order Tests ────────────────────────────


class TestLookupOrder:
    def test_existing_order(self):
        result = lookup_order("ORD-1025")
        assert result["success"] is True
        assert result["found"] is True
        order = result["order"]
        assert order is not None
        assert order["customer_name"] == "Karthik Rao"
        assert order["city"] == "Kochi"
        assert order["product"] == "Wireless Mouse"
        assert order["total_inr"] == 2397
        assert order["status"] == "delivered"
        assert order["order_date"] == "2026-07-14"

    def test_nonexistent_order(self):
        result = lookup_order("ORD-9999")
        assert result["success"] is True
        assert result["found"] is False
        assert result["order"] is None
        assert "not found" in result["message"].lower()

    def test_empty_order_id(self):
        result = lookup_order("")
        assert result["success"] is False
        assert result["found"] is False
        assert result["order"] is None

    def test_whitespace_padded_order_id(self):
        result = lookup_order("  ORD-1025  ")
        assert result["success"] is True
        assert result["found"] is True
        assert result["order"]["order_id"] == "ORD-1025"

    def test_case_insensitive_lookup(self):
        result = lookup_order("ord-1025")
        assert result["success"] is True
        assert result["found"] is True
        assert result["order"]["order_id"] == "ORD-1025"


# ──────────────────────────── analyze_orders Tests ────────────────────────────


class TestAnalyzeOrders:
    def test_cancelled_count(self, raw_df):
        expected_count = int((raw_df["_status"] == "cancelled").sum())
        assert expected_count == 7  # Sanity check §0.3

        result = analyze_orders(operation="count_orders", status="cancelled")
        assert result["success"] is True
        assert result["operation"] == "count_orders"
        assert result["count"] == 7
        assert result["matched_count"] == 7
        assert result["empty"] is False
        assert result["applied_filters"] == {"status": "cancelled"}

    def test_electronics_august_revenue(self, raw_df):
        # Sanity check §0.3: Electronics Aug 2026 = 4 orders, ₹27,189
        mask = (
            (raw_df["_category"] == "electronics")
            & (raw_df["order_date"] >= pd.Timestamp("2026-08-01"))
            & (raw_df["order_date"] <= pd.Timestamp("2026-08-31"))
        )
        expected_revenue = int(raw_df.loc[mask, "total_inr"].sum())
        expected_count = int(mask.sum())
        assert expected_count == 4
        assert expected_revenue == 27189

        result = analyze_orders(
            operation="sum_revenue",
            category="Electronics",
            start_date="2026-08-01",
            end_date="2026-08-31",
        )
        assert result["success"] is True
        assert result["total_revenue_inr"] == 27189
        assert result["matched_count"] == 4
        assert result["empty"] is False

    def test_top_customer(self, raw_df):
        # Sanity check §0.3: Rohan Das, ₹1,12,282
        grouped = raw_df.groupby("customer_name")["total_inr"].sum()
        expected_top = grouped.idxmax()
        expected_total = int(grouped.max())
        assert expected_top == "Rohan Das"
        assert expected_total == 112282

        result = analyze_orders(operation="top_customer")
        assert result["success"] is True
        assert result["empty"] is False
        assert len(result["top_customers"]) >= 1
        top_1 = result["top_customers"][0]
        assert top_1["customer_name"] == "Rohan Das"
        assert top_1["total_spent_inr"] == 112282

    def test_boundary_dates_inclusive(self, raw_df):
        # Boundary dates 1 Aug and 31 Aug inclusive
        aug_orders = raw_df[
            (raw_df["order_date"] >= pd.Timestamp("2026-08-01"))
            & (raw_df["order_date"] <= pd.Timestamp("2026-08-31"))
        ]
        expected_count = len(aug_orders)

        result = analyze_orders(
            operation="count_orders",
            start_date="2026-08-01",
            end_date="2026-08-31",
        )
        assert result["success"] is True
        assert result["count"] == expected_count

    def test_category_and_status_combined(self, raw_df):
        mask = (raw_df["_category"] == "electronics") & (raw_df["_status"] == "delivered")
        expected_count = int(mask.sum())
        expected_rev = int(raw_df.loc[mask, "total_inr"].sum())

        count_res = analyze_orders(
            operation="count_orders",
            category="Electronics",
            status="delivered",
        )
        assert count_res["count"] == expected_count

        rev_res = analyze_orders(
            operation="sum_revenue",
            category="Electronics",
            status="delivered",
        )
        assert rev_res["total_revenue_inr"] == expected_rev

    def test_empty_result(self):
        result = analyze_orders(operation="count_orders", category="NonExistentCategory")
        assert result["success"] is True
        assert result["count"] == 0
        assert result["empty"] is True

        rev_res = analyze_orders(operation="sum_revenue", city="Atlantis")
        assert rev_res["success"] is True
        assert rev_res["total_revenue_inr"] == 0
        assert rev_res["empty"] is True

        cust_res = analyze_orders(operation="top_customer", city="Atlantis")
        assert cust_res["success"] is True
        assert cust_res["top_customers"] == []
        assert cust_res["empty"] is True

    def test_invalid_date_format(self):
        result = analyze_orders(operation="count_orders", start_date="2026/08/01")
        assert result["success"] is False
        assert "invalid start_date" in result["error"].lower()

        res_bad_cal = analyze_orders(operation="count_orders", end_date="2026-02-31")
        assert res_bad_cal["success"] is False
        assert "invalid calendar date" in res_bad_cal["error"].lower()

    def test_start_greater_than_end_date(self):
        result = analyze_orders(
            operation="count_orders",
            start_date="2026-09-01",
            end_date="2026-08-01",
        )
        assert result["success"] is False
        assert "cannot be greater than" in result["error"].lower()

    def test_unsupported_operation(self):
        result = analyze_orders(operation="invalid_op")
        assert result["success"] is False
        assert "unknown operation" in result["error"].lower()

    def test_revenue_uses_total_inr_and_count_not_quantity_sum(self, raw_df):
        total_rows = len(raw_df)  # 60
        total_qty = int(raw_df["quantity"].sum())  # > 60
        total_rev = int(raw_df["total_inr"].sum())

        assert total_rows != total_qty, "Total rows must not equal total quantity"

        count_res = analyze_orders(operation="count_orders")
        assert count_res["count"] == total_rows
        assert count_res["count"] != total_qty

        rev_res = analyze_orders(operation="sum_revenue")
        assert rev_res["total_revenue_inr"] == total_rev

    def test_list_orders_truncation_and_fields(self):
        result = analyze_orders(operation="list_orders")
        assert result["success"] is True
        assert result["total_matches"] == 60
        assert result["matched_count"] == 60
        assert result["truncated"] is True
        assert len(result["orders"]) == 25
        first_order = result["orders"][0]
        assert "order_id" in first_order
        assert "order_date" in first_order
        assert "total_inr" in first_order


# ──────────────────────────── dispatch_tool Tests ────────────────────────────


class TestDispatchTool:
    def test_dispatch_lookup(self):
        result = dispatch_tool("lookup_order", {"order_id": "ORD-1025"})
        assert result["success"] is True
        assert result["found"] is True
        assert result["order"]["customer_name"] == "Karthik Rao"

    def test_dispatch_analyze(self):
        result = dispatch_tool("analyze_orders", {"operation": "count_orders", "status": "cancelled"})
        assert result["success"] is True
        assert result["count"] == 7

    def test_dispatch_unknown_tool(self):
        result = dispatch_tool("unknown_magic_tool", {})
        assert result["success"] is False
        assert "unknown tool" in result["error"].lower()

    def test_dispatch_invalid_args_type(self):
        result = dispatch_tool("lookup_order", "not-a-dict")  # type: ignore
        assert result["success"] is False
        assert "dictionary" in result["error"].lower()
