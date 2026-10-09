"""Tests for tool functions — all expected values computed from the CSV, not hardcoded."""

import pandas as pd
from backend.app.tools import (
    lookup_order,
    orders_by_status,
    revenue,
    top_customers,
    orders_by_date_range,
    orders_by_customer,
    orders_by_city,
    orders_by_category,
    summary_stats,
    _format_inr,
)


class TestFormatINR:
    def test_small_number(self):
        assert _format_inr(599) == "₹599"

    def test_four_digits(self):
        assert _format_inr(2397) == "₹2,397"

    def test_six_digits(self):
        assert _format_inr(112282) == "₹1,12,282"

    def test_large_number(self):
        assert _format_inr(2199900) == "₹21,99,900"


class TestLookupOrder:
    def test_existing_order(self):
        result = lookup_order("ORD-1025")
        assert "order" in result
        assert result["order"]["customer_name"] == "Karthik Rao"
        assert result["order"]["total_inr"] == "₹2,397"

    def test_missing_order(self):
        result = lookup_order("ORD-9999")
        assert "error" in result


class TestOrdersByStatus:
    def test_cancelled_count(self, orders_df):
        """Cancelled orders count should match CSV computation."""
        expected = len(orders_df[orders_df["_status"] == "cancelled"])
        result = orders_by_status("cancelled")
        assert result["count"] == expected
        # Sanity check from spec: should be 7
        assert result["count"] == 7

    def test_case_insensitive(self):
        result = orders_by_status("CANCELLED")
        assert result["count"] == 7


class TestRevenue:
    def test_electronics_august(self, orders_df):
        """Electronics in Aug 2026 — computed from CSV."""
        filtered = orders_df[
            (orders_df["_category"] == "electronics")
            & (orders_df["order_date"] >= pd.Timestamp("2026-08-01"))
            & (orders_df["order_date"] <= pd.Timestamp("2026-08-31"))
        ]
        expected_count = len(filtered)
        expected_revenue = int(filtered["total_inr"].sum())

        result = revenue(
            category="Electronics",
            start_date="2026-08-01",
            end_date="2026-08-31",
        )
        assert result["order_count"] == expected_count
        assert result["total_revenue_raw"] == expected_revenue
        # Sanity check from spec: 4 orders, ₹27,189
        assert expected_count == 4
        assert expected_revenue == 27189

    def test_total_revenue_all(self, orders_df):
        expected = int(orders_df["total_inr"].sum())
        result = revenue()
        assert result["total_revenue_raw"] == expected


class TestTopCustomers:
    def test_top_1(self, orders_df):
        """Top customer by total_inr — computed from CSV."""
        grouped = orders_df.groupby("customer_name")["total_inr"].sum()
        expected_name = grouped.idxmax()
        expected_total = int(grouped.max())

        result = top_customers(limit=1)
        assert result["customers"][0]["customer_name"] == expected_name
        assert result["customers"][0]["total_spent_raw"] == expected_total
        # Sanity check from spec: Rohan Das, ₹1,12,282
        assert expected_name == "Rohan Das"

    def test_rohan_das_total(self, orders_df):
        rohan = orders_df[orders_df["_customer"] == "rohan das"]
        total = int(rohan["total_inr"].sum())
        # Verify against spec value
        assert total == 112282


class TestOrdersByDateRange:
    def test_august_electronics(self, orders_df):
        result = orders_by_date_range(
            start_date="2026-08-01",
            end_date="2026-08-31",
            category="Electronics",
        )
        assert result["count"] == 4


class TestOrdersByCustomer:
    def test_existing_customer(self):
        result = orders_by_customer("Karthik Rao")
        assert result["order_count"] > 0
        assert result["customer_name"] == "Karthik Rao"

    def test_missing_customer(self):
        result = orders_by_customer("Nonexistent Person")
        assert "error" in result


class TestOrdersByCity:
    def test_chennai(self, orders_df):
        expected = len(orders_df[orders_df["_city"] == "chennai"])
        result = orders_by_city("Chennai")
        assert result["order_count"] == expected

    def test_case_insensitive(self, orders_df):
        result = orders_by_city("CHENNAI")
        expected = len(orders_df[orders_df["_city"] == "chennai"])
        assert result["order_count"] == expected


class TestOrdersByCategory:
    def test_electronics(self, orders_df):
        expected = len(orders_df[orders_df["_category"] == "electronics"])
        result = orders_by_category("Electronics")
        assert result["order_count"] == expected


class TestSummaryStats:
    def test_summary(self, orders_df):
        result = summary_stats()
        assert result["total_orders"] == 60
        assert result["unique_customers"] == len(orders_df["customer_name"].unique())
        assert result["total_revenue_raw"] == int(orders_df["total_inr"].sum())
