"""
Deterministic tool functions that operate on the in-memory DataFrame.
The LLM never does math — these functions do all computation.
"""

import pandas as pd
from typing import Any
from .data_loader import get_orders


def _format_inr(value: int | float | Any) -> str:
    """Format number with Indian grouping and ₹ symbol.
    E.g. 112282 → '₹1,12,282'
    """
    try:
        f_val = float(value)
        if f_val == int(f_val):
            value = int(f_val)
    except (ValueError, TypeError):
        pass

    if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
        s = str(int(value))
        if len(s) <= 3:
            return f"₹{s}"
        # Last 3 digits, then groups of 2
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while rest:
            groups.append(rest[-2:])
            rest = rest[:-2]
        groups.reverse()
        return f"₹{','.join(groups)},{last3}"
    else:
        # Float with decimals
        int_part = int(value)
        dec_part = f"{value - int_part:.2f}"[1:]  # ".xx"
        formatted_int = _format_inr(int_part).replace("₹", "")
        return f"₹{formatted_int}{dec_part}"


def _format_date(dt: pd.Timestamp) -> str:
    """Format date as '14 Jul 2026'."""
    return dt.strftime("%-d %b %Y") if hasattr(dt, "strftime") else str(dt)


def _safe_format_date(dt: Any) -> str:
    """Try to format date, fall back to string."""
    try:
        return _format_date(dt)
    except (ValueError, AttributeError):
        # Windows doesn't support %-d, use %#d instead
        try:
            return dt.strftime("%#d %b %Y")
        except (ValueError, AttributeError):
            return str(dt)


def _order_to_dict(row: pd.Series) -> dict:
    """Convert a DataFrame row to a clean dict for the LLM."""
    return {
        "order_id": row["order_id"],
        "order_date": _safe_format_date(row["order_date"]),
        "customer_name": row["customer_name"],
        "city": row["city"],
        "product": row["product"],
        "category": row["category"],
        "quantity": int(row["quantity"]),
        "unit_price_inr": _format_inr(row["unit_price_inr"]),
        "total_inr": _format_inr(row["total_inr"]),
        "payment_method": row["payment_method"],
        "status": row["status"],
    }


def _apply_filters(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Apply optional filters (category, city, status, date range)."""
    if kwargs.get("category"):
        df = df[df["_category"] == kwargs["category"].strip().casefold()]
    if kwargs.get("city"):
        df = df[df["_city"] == kwargs["city"].strip().casefold()]
    if kwargs.get("status"):
        df = df[df["_status"] == kwargs["status"].strip().casefold()]
    if kwargs.get("start_date"):
        df = df[df["order_date"] >= pd.Timestamp(kwargs["start_date"])]
    if kwargs.get("end_date"):
        df = df[df["order_date"] <= pd.Timestamp(kwargs["end_date"])]
    return df


# ──────────────────────────── Tool Functions ────────────────────────────


def lookup_order(order_id: str) -> dict:
    """Look up a specific order by its ID."""
    df = get_orders()
    matches = df[df["order_id"] == order_id.strip().upper()]
    if matches.empty:
        return {"error": f"Order {order_id} not found.", "order_id": order_id}
    return {"order": _order_to_dict(matches.iloc[0])}


def orders_by_status(status: str) -> dict:
    """Get all orders with a given status."""
    df = get_orders()
    normalized = status.strip().casefold()
    matches = df[df["_status"] == normalized]
    orders = [_order_to_dict(row) for _, row in matches.iterrows()]
    return {
        "status": status,
        "count": len(orders),
        "orders": orders,
    }


def revenue(
    category: str | None = None,
    city: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    status: str | None = None,
) -> dict:
    """Calculate total revenue (sum of total_inr) with optional filters.
    Revenue includes all statuses by default unless a status filter is given.
    """
    df = get_orders()
    filtered = _apply_filters(
        df, category=category, city=city, status=status,
        start_date=start_date, end_date=end_date,
    )
    total = int(filtered["total_inr"].sum())
    result: dict[str, Any] = {
        "total_revenue": _format_inr(total),
        "total_revenue_raw": total,
        "order_count": len(filtered),
        "definition": "Sum of total_inr for matching orders. All statuses included unless explicitly filtered.",
    }
    # Add active filters to result for clarity
    filters_applied = {}
    if category:
        filters_applied["category"] = category
    if city:
        filters_applied["city"] = city
    if start_date:
        filters_applied["start_date"] = start_date
    if end_date:
        filters_applied["end_date"] = end_date
    if status:
        filters_applied["status"] = status
    if filters_applied:
        result["filters_applied"] = filters_applied
    return result


def top_customers(
    limit: int = 5,
    category: str | None = None,
    status: str | None = None,
) -> dict:
    """Get top customers by total spending.
    All statuses included by default. Ties are returned.
    """
    df = get_orders()
    filtered = _apply_filters(df, category=category, status=status)
    grouped = filtered.groupby("customer_name")["total_inr"].sum().reset_index()
    grouped = grouped.sort_values("total_inr", ascending=False)

    if grouped.empty:
        return {"customers": [], "count": 0}

    # Handle ties: get the Nth highest value, include all with that value
    top = grouped.head(limit)
    cutoff = top["total_inr"].min()
    with_ties = grouped[grouped["total_inr"] >= cutoff]

    has_tie = len(with_ties) > limit
    customers = []
    for _, row in with_ties.iterrows():
        customers.append({
            "customer_name": row["customer_name"],
            "total_spent": _format_inr(int(row["total_inr"])),
            "total_spent_raw": int(row["total_inr"]),
        })

    return {
        "customers": customers,
        "count": len(customers),
        "tie": has_tie,
        "definition": "Grouped by customer_name, sum of total_inr, all statuses included.",
    }


def orders_by_date_range(
    start_date: str,
    end_date: str,
    category: str | None = None,
    city: str | None = None,
    status: str | None = None,
) -> dict:
    """Get orders within a date range with optional filters."""
    df = get_orders()
    filtered = _apply_filters(
        df, category=category, city=city, status=status,
        start_date=start_date, end_date=end_date,
    )
    orders = [_order_to_dict(row) for _, row in filtered.iterrows()]
    return {
        "start_date": start_date,
        "end_date": end_date,
        "count": len(orders),
        "orders": orders,
    }


def orders_by_customer(customer_name: str) -> dict:
    """Get all orders for a specific customer."""
    df = get_orders()
    normalized = customer_name.strip().casefold()
    matches = df[df["_customer"] == normalized]
    if matches.empty:
        return {
            "error": f"No orders found for customer '{customer_name}'.",
            "customer_name": customer_name,
        }
    orders = [_order_to_dict(row) for _, row in matches.iterrows()]
    total_spent = int(matches["total_inr"].sum())
    return {
        "customer_name": matches.iloc[0]["customer_name"],  # original case
        "order_count": len(orders),
        "total_spent": _format_inr(total_spent),
        "total_spent_raw": total_spent,
        "orders": orders,
    }


def orders_by_city(city: str) -> dict:
    """Get all orders from a specific city."""
    df = get_orders()
    normalized = city.strip().casefold()
    matches = df[df["_city"] == normalized]
    if matches.empty:
        return {"error": f"No orders found for city '{city}'.", "city": city}
    orders = [_order_to_dict(row) for _, row in matches.iterrows()]
    return {
        "city": matches.iloc[0]["city"],  # original case
        "order_count": len(orders),
        "orders": orders,
    }


def orders_by_category(category: str) -> dict:
    """Get all orders in a specific category."""
    df = get_orders()
    normalized = category.strip().casefold()
    matches = df[df["_category"] == normalized]
    if matches.empty:
        return {
            "error": f"No orders found for category '{category}'.",
            "category": category,
        }
    orders = [_order_to_dict(row) for _, row in matches.iterrows()]
    total_revenue = int(matches["total_inr"].sum())
    return {
        "category": matches.iloc[0]["category"],  # original case
        "order_count": len(orders),
        "total_revenue": _format_inr(total_revenue),
        "total_revenue_raw": total_revenue,
        "orders": orders,
    }


def summary_stats() -> dict:
    """Get overall summary statistics of all orders."""
    df = get_orders()
    total_orders = len(df)
    total_revenue = int(df["total_inr"].sum())
    unique_customers = df["customer_name"].nunique()
    unique_products = df["product"].nunique()

    status_counts = df["status"].value_counts().to_dict()
    category_counts = df["category"].value_counts().to_dict()
    city_counts = df["city"].value_counts().to_dict()

    date_range = {
        "earliest": _safe_format_date(df["order_date"].min()),
        "latest": _safe_format_date(df["order_date"].max()),
    }

    return {
        "total_orders": total_orders,
        "total_revenue": _format_inr(total_revenue),
        "total_revenue_raw": total_revenue,
        "unique_customers": unique_customers,
        "unique_products": unique_products,
        "status_breakdown": status_counts,
        "category_breakdown": category_counts,
        "city_breakdown": city_counts,
        "date_range": date_range,
    }


# ──────────────────────────── Tool Registry ────────────────────────────

TOOL_REGISTRY: dict[str, callable] = {
    "lookup_order": lookup_order,
    "orders_by_status": orders_by_status,
    "revenue": revenue,
    "top_customers": top_customers,
    "orders_by_date_range": orders_by_date_range,
    "orders_by_customer": orders_by_customer,
    "orders_by_city": orders_by_city,
    "orders_by_category": orders_by_category,
    "summary_stats": summary_stats,
}
