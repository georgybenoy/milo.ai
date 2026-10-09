"""
Deterministic tool functions for Milo.
The LLM never does math — these functions perform all computation deterministically.
"""

from datetime import datetime
import re
from typing import Any
import pandas as pd

from .data_loader import get_orders

try:
    from google.genai import types
    _HAS_GENAI = True
except ImportError:
    _HAS_GENAI = False


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
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while rest:
            groups.append(rest[-2:])
            rest = rest[:-2]
        groups.reverse()
        return f"₹{','.join(groups)},{last3}"
    else:
        int_part = int(value)
        dec_part = f"{value - int_part:.2f}"[1:]
        formatted_int = _format_inr(int_part).replace("₹", "")
        return f"₹{formatted_int}{dec_part}"


def _order_to_dict(row: pd.Series) -> dict[str, Any]:
    """Serialize a DataFrame row to a clean dict with ISO date."""
    dt = pd.to_datetime(row["order_date"])
    unit_price = float(row["unit_price_inr"])
    total = float(row["total_inr"])
    return {
        "order_id": str(row["order_id"]),
        "order_date": dt.strftime("%Y-%m-%d"),
        "customer_name": str(row["customer_name"]),
        "city": str(row["city"]),
        "product": str(row["product"]),
        "category": str(row["category"]),
        "quantity": int(row["quantity"]),
        "unit_price_inr": int(unit_price) if unit_price.is_integer() else unit_price,
        "total_inr": int(total) if total.is_integer() else total,
        "formatted_total_inr": _format_inr(total),
        "payment_method": str(row["payment_method"]),
        "status": str(row["status"]),
    }


def lookup_order(order_id: str) -> dict[str, Any]:
    """Lookup a single specific order by its order ID.

    Validates non-empty string, max ~32 chars, strips whitespace, exact match (case-insensitive).
    Returns {success, found, order, message}. Dates are serialized as ISO strings.
    """
    if not isinstance(order_id, str):
        return {
            "success": False,
            "found": False,
            "order": None,
            "message": "order_id must be a string.",
        }

    clean_id = order_id.strip()
    if not clean_id or len(clean_id) > 32:
        return {
            "success": False,
            "found": False,
            "order": None,
            "message": "order_id must be a non-empty string with maximum 32 characters.",
        }

    df = get_orders()
    matches = df[df["order_id"].astype(str).str.strip().str.casefold() == clean_id.casefold()]

    if matches.empty:
        return {
            "success": True,
            "found": False,
            "order": None,
            "message": f"Order '{clean_id}' not found.",
        }

    order_data = _order_to_dict(matches.iloc[0])
    return {
        "success": True,
        "found": True,
        "order": order_data,
        "message": f"Order '{order_data['order_id']}' retrieved successfully.",
    }


ALLOWED_OPERATIONS = {"count_orders", "sum_revenue", "top_customer", "list_orders"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def analyze_orders(
    operation: str,
    status: str | None = None,
    category: str | None = None,
    customer_name: str | None = None,
    city: str | None = None,
    product: str | None = None,
    payment_method: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Analyze and query orders dataset.

    Operations:
    - count_orders: count matching rows (not quantity sum)
    - sum_revenue: sum total_inr (all statuses unless filtered)
    - top_customer: customer with highest total_inr (handles ties)
    - list_orders: returns matching orders capped at 25
    """
    if not isinstance(operation, str) or operation.strip() not in ALLOWED_OPERATIONS:
        return {
            "success": False,
            "error": f"Unknown operation '{operation}'. Allowed operations: {sorted(ALLOWED_OPERATIONS)}",
        }

    operation = operation.strip()

    # Validate filter types
    filters_to_check = {
        "status": status,
        "category": category,
        "customer_name": customer_name,
        "city": city,
        "product": product,
        "payment_method": payment_method,
        "start_date": start_date,
        "end_date": end_date,
    }
    for filter_name, filter_val in filters_to_check.items():
        if filter_val is not None and not isinstance(filter_val, str):
            return {
                "success": False,
                "error": f"Invalid type for filter '{filter_name}': expected string, got {type(filter_val).__name__}.",
            }

    # Validate dates
    parsed_start_dt = None
    parsed_end_dt = None

    if start_date is not None and start_date.strip():
        sd_str = start_date.strip()
        if not DATE_PATTERN.match(sd_str):
            return {
                "success": False,
                "error": f"Invalid start_date '{start_date}'. Must be in YYYY-MM-DD format.",
            }
        try:
            parsed_start_dt = datetime.strptime(sd_str, "%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid calendar date for start_date '{start_date}'.",
            }

    if end_date is not None and end_date.strip():
        ed_str = end_date.strip()
        if not DATE_PATTERN.match(ed_str):
            return {
                "success": False,
                "error": f"Invalid end_date '{end_date}'. Must be in YYYY-MM-DD format.",
            }
        try:
            parsed_end_dt = datetime.strptime(ed_str, "%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid calendar date for end_date '{end_date}'.",
            }

    if parsed_start_dt and parsed_end_dt and parsed_start_dt > parsed_end_dt:
        return {
            "success": False,
            "error": f"start_date ({start_date}) cannot be greater than end_date ({end_date}).",
        }

    df = get_orders()
    applied_filters: dict[str, str] = {}

    # Apply only explicitly supplied filters
    if status is not None and status.strip():
        s_val = status.strip()
        df = df[df["_status"] == s_val.casefold()]
        applied_filters["status"] = s_val

    if category is not None and category.strip():
        cat_val = category.strip()
        df = df[df["_category"] == cat_val.casefold()]
        applied_filters["category"] = cat_val

    if customer_name is not None and customer_name.strip():
        cust_val = customer_name.strip()
        df = df[df["_customer"] == cust_val.casefold()]
        applied_filters["customer_name"] = cust_val

    if city is not None and city.strip():
        city_val = city.strip()
        df = df[df["_city"] == city_val.casefold()]
        applied_filters["city"] = city_val

    if product is not None and product.strip():
        prod_val = product.strip()
        df = df[df["_product"] == prod_val.casefold()]
        applied_filters["product"] = prod_val

    if payment_method is not None and payment_method.strip():
        pm_val = payment_method.strip()
        df = df[df["_payment"] == pm_val.casefold()]
        applied_filters["payment_method"] = pm_val

    if parsed_start_dt:
        df = df[df["order_date"] >= pd.Timestamp(parsed_start_dt)]
        applied_filters["start_date"] = start_date.strip()

    if parsed_end_dt:
        df = df[df["order_date"] <= pd.Timestamp(parsed_end_dt)]
        applied_filters["end_date"] = end_date.strip()

    matched_count = len(df)
    is_empty = matched_count == 0

    if operation == "count_orders":
        return {
            "success": True,
            "operation": "count_orders",
            "count": matched_count,
            "matched_count": matched_count,
            "applied_filters": applied_filters,
            "empty": is_empty,
        }

    elif operation == "sum_revenue":
        total_revenue = float(df["total_inr"].sum()) if not is_empty else 0.0
        cleaned_rev = int(total_revenue) if total_revenue.is_integer() else total_revenue
        return {
            "success": True,
            "operation": "sum_revenue",
            "total_revenue_inr": cleaned_rev,
            "formatted_total_revenue_inr": _format_inr(cleaned_rev),
            "matched_count": matched_count,
            "applied_filters": applied_filters,
            "empty": is_empty,
        }

    elif operation == "top_customer":
        if is_empty:
            return {
                "success": True,
                "operation": "top_customer",
                "top_customers": [],
                "matched_count": 0,
                "applied_filters": applied_filters,
                "empty": True,
            }

        grouped = df.groupby("customer_name")["total_inr"].sum().reset_index()
        max_spent = grouped["total_inr"].max()
        top_group = grouped[grouped["total_inr"] == max_spent]

        top_customers = []
        for _, row in top_group.iterrows():
            c_name = row["customer_name"]
            c_tot = float(row["total_inr"])
            c_tot_clean = int(c_tot) if c_tot.is_integer() else c_tot
            c_orders = int((df["customer_name"] == c_name).sum())
            top_customers.append({
                "customer_name": c_name,
                "total_spent_inr": c_tot_clean,
                "formatted_total_spent_inr": _format_inr(c_tot_clean),
                "order_count": c_orders,
            })

        max_clean = int(max_spent) if float(max_spent).is_integer() else float(max_spent)
        return {
            "success": True,
            "operation": "top_customer",
            "top_customers": top_customers,
            "max_revenue_inr": max_clean,
            "matched_count": matched_count,
            "applied_filters": applied_filters,
            "empty": False,
        }

    elif operation == "list_orders":
        cap = 25
        truncated = matched_count > cap
        rows = df.head(cap)
        orders_list = [_order_to_dict(row) for _, row in rows.iterrows()]
        return {
            "success": True,
            "operation": "list_orders",
            "orders": orders_list,
            "total_matches": matched_count,
            "matched_count": matched_count,
            "truncated": truncated,
            "limit": cap,
            "applied_filters": applied_filters,
            "empty": is_empty,
        }

    return {
        "success": False,
        "error": f"Unhandled operation '{operation}'.",
    }


# ──────────────────────────── Tool Dispatcher ────────────────────────────

TOOL_REGISTRY = {
    "lookup_order": lookup_order,
    "analyze_orders": analyze_orders,
}


def dispatch_tool(name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate tool name, dispatch to function, and wrap exceptions in structured error."""
    if not isinstance(name, str) or name not in TOOL_REGISTRY:
        return {
            "success": False,
            "error": f"Unknown tool '{name}'. Available tools: {sorted(TOOL_REGISTRY.keys())}",
        }
    if args is None:
        args = {}
    if not isinstance(args, dict):
        return {
            "success": False,
            "error": f"Tool arguments must be a dictionary, got {type(args).__name__}.",
        }

    tool_fn = TOOL_REGISTRY[name]
    try:
        return tool_fn(**args)
    except TypeError as e:
        return {
            "success": False,
            "error": f"Invalid arguments for tool '{name}': {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool execution failed in '{name}': {e}",
        }


# ──────────────────────────── Gemini Tool Declarations ────────────────────────────

GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "lookup_order",
        "description": (
            "Lookup details for a single specific order by its order ID (e.g. 'ORD-1025'). "
            "ROUTING RULE: Use this tool whenever the user asks about a specific order ID. "
            "Do NOT use this tool for aggregate counts, revenue, top customers, or listings."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "order_id": {
                    "type": "STRING",
                    "description": "The exact order ID to look up (e.g. 'ORD-1025').",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "analyze_orders",
        "description": (
            "Analyze and query orders with deterministic analytics. "
            "ROUTING RULES: "
            "1. Use operation='count_orders' to count matching orders/transactions (counts rows, not quantity sum). "
            "2. Use operation='sum_revenue' to calculate total revenue in INR. Revenue is the sum of recorded total_inr "
            "   across matching orders, including cancelled and returned orders unless the user explicitly filters by status. "
            "3. Use operation='top_customer' to identify the highest spending customer by total_inr (handles ties). "
            "4. Use operation='list_orders' to retrieve details for orders matching criteria (capped at 25). "
            "Apply only explicitly requested filters: status, category, customer_name, city, product, payment_method, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "operation": {
                    "type": "STRING",
                    "enum": ["count_orders", "sum_revenue", "top_customer", "list_orders"],
                    "description": "The analytics operation to perform.",
                },
                "status": {
                    "type": "STRING",
                    "description": "Filter by order status (e.g. Delivered, Cancelled, Returned, Processing, Shipped).",
                },
                "category": {
                    "type": "STRING",
                    "description": "Filter by product category (e.g. Electronics, Clothing, Home, Books).",
                },
                "customer_name": {
                    "type": "STRING",
                    "description": "Filter by customer name (e.g. Rohan Das, Karthik Rao).",
                },
                "city": {
                    "type": "STRING",
                    "description": "Filter by delivery city (e.g. Mumbai, Delhi, Bengaluru, Chennai, Pune, Kolkata).",
                },
                "product": {
                    "type": "STRING",
                    "description": "Filter by specific product name.",
                },
                "payment_method": {
                    "type": "STRING",
                    "description": "Filter by payment method (e.g. Credit Card, UPI, Debit Card, Net Banking, Cash on Delivery).",
                },
                "start_date": {
                    "type": "STRING",
                    "description": "Start of date range in YYYY-MM-DD format (inclusive).",
                },
                "end_date": {
                    "type": "STRING",
                    "description": "End of date range in YYYY-MM-DD format (inclusive).",
                },
            },
            "required": ["operation"],
        },
    },
]

if _HAS_GENAI:
    GEMINI_FUNCTION_DECLARATIONS = [
        types.FunctionDeclaration(
            name="lookup_order",
            description=(
                "Lookup details for a single specific order by its order ID (e.g. 'ORD-1025'). "
                "ROUTING RULE: Use this tool whenever the user asks about a specific order ID. "
                "Do NOT use this tool for aggregate counts, revenue, top customers, or listings."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "order_id": types.Schema(
                        type=types.Type.STRING,
                        description="The exact order ID to look up (e.g. 'ORD-1025').",
                    ),
                },
                required=["order_id"],
            ),
        ),
        types.FunctionDeclaration(
            name="analyze_orders",
            description=(
                "Analyze and query orders with deterministic analytics. "
                "ROUTING RULES: "
                "1. Use operation='count_orders' to count matching orders/transactions (counts rows, not quantity sum). "
                "2. Use operation='sum_revenue' to calculate total revenue in INR. Revenue is the sum of recorded total_inr "
                "   across matching orders, including cancelled and returned orders unless the user explicitly filters by status. "
                "3. Use operation='top_customer' to identify the highest spending customer by total_inr (handles ties). "
                "4. Use operation='list_orders' to retrieve details for orders matching criteria (capped at 25). "
                "Apply only explicitly requested filters: status, category, customer_name, city, product, payment_method, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "operation": types.Schema(
                        type=types.Type.STRING,
                        enum=["count_orders", "sum_revenue", "top_customer", "list_orders"],
                        description="The analytics operation to perform.",
                    ),
                    "status": types.Schema(
                        type=types.Type.STRING,
                        description="Filter by order status (e.g. Delivered, Cancelled, Returned, Processing, Shipped).",
                    ),
                    "category": types.Schema(
                        type=types.Type.STRING,
                        description="Filter by product category (e.g. Electronics, Clothing, Home, Books).",
                    ),
                    "customer_name": types.Schema(
                        type=types.Type.STRING,
                        description="Filter by customer name (e.g. Rohan Das, Karthik Rao).",
                    ),
                    "city": types.Schema(
                        type=types.Type.STRING,
                        description="Filter by delivery city (e.g. Mumbai, Delhi, Bengaluru, Chennai, Pune, Kolkata).",
                    ),
                    "product": types.Schema(
                        type=types.Type.STRING,
                        description="Filter by specific product name.",
                    ),
                    "payment_method": types.Schema(
                        type=types.Type.STRING,
                        description="Filter by payment method (e.g. Credit Card, UPI, Debit Card, Net Banking, Cash on Delivery).",
                    ),
                    "start_date": types.Schema(
                        type=types.Type.STRING,
                        description="Start of date range in YYYY-MM-DD format (inclusive).",
                    ),
                    "end_date": types.Schema(
                        type=types.Type.STRING,
                        description="End of date range in YYYY-MM-DD format (inclusive).",
                    ),
                },
                required=["operation"],
            ),
        ),
    ]
else:
    GEMINI_FUNCTION_DECLARATIONS = []
