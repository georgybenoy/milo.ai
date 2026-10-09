"""
Milo Agent — Gemini function calling with tool execution loop.
Uses the official google-genai SDK with native function calling.
No LangChain. No agent frameworks.
"""

import json
import logging
from typing import Any
from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_MODEL, MAX_TOOL_ITERATIONS
from .tools import TOOL_REGISTRY

logger = logging.getLogger(__name__)

# ──────────────────────────── System Prompt ────────────────────────────

SYSTEM_PROMPT = """You are Milo, an AI assistant for order intelligence. You help users answer questions about their orders data.

IMPORTANT RULES:
1. You MUST use the provided tools to answer questions about orders. NEVER invent order data or do math yourself.
2. When reporting revenue, state that it is the sum of total_inr for matching orders, with all statuses included unless the user asks for a specific status filter. Never call it "net revenue" or "realised revenue".
3. For top customer queries, group by customer_name and sum total_inr. All statuses are included by default. If there are ties, mention them.
4. "August" means August 2026 (2026-08-01 to 2026-08-31). Similarly for other months — the data spans June to September 2026.
5. Display currency in Indian format with ₹ (e.g., ₹1,12,282). The tool results already format this for you.
6. Display dates as "14 Jul 2026" format.
7. If a tool returns an error, report it honestly. Never claim a tool succeeded if it errored. Never fabricate a record for a missing order.
8. Be concise, helpful, and friendly. Use markdown formatting for readability.
9. When listing multiple orders, use a clean table or bullet format.
10. If you're unsure which tool to use, ask the user for clarification rather than guessing.

AVAILABLE DATA:
- 60 orders (ORD-1001 to ORD-1060)
- Date range: June 2026 to September 2026
- Categories: Electronics, Accessories, Stationery, Furniture
- Statuses: delivered, cancelled, returned, processing, shipped
- Cities: Hyderabad, Pune, Bengaluru, Chennai, Kochi, Thiruvananthapuram
"""

# ──────────────────────────── Tool Declarations ────────────────────────

TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="lookup_order",
        description="Look up a specific order by its order ID (e.g. ORD-1025). Returns full order details.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "order_id": types.Schema(
                    type=types.Type.STRING,
                    description="The order ID to look up, e.g. 'ORD-1025'",
                ),
            },
            required=["order_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="orders_by_status",
        description="Get all orders with a given status. Valid statuses: delivered, cancelled, returned, processing, shipped.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "status": types.Schema(
                    type=types.Type.STRING,
                    description="Order status to filter by (delivered/cancelled/returned/processing/shipped)",
                ),
            },
            required=["status"],
        ),
    ),
    types.FunctionDeclaration(
        name="revenue",
        description="Calculate total revenue (sum of total_inr) with optional filters. Revenue includes ALL statuses by default unless a status filter is explicitly provided. Never call it 'net revenue'.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "category": types.Schema(
                    type=types.Type.STRING,
                    description="Filter by category (Electronics/Accessories/Stationery/Furniture)",
                ),
                "city": types.Schema(
                    type=types.Type.STRING,
                    description="Filter by city",
                ),
                "start_date": types.Schema(
                    type=types.Type.STRING,
                    description="Start date in YYYY-MM-DD format (inclusive)",
                ),
                "end_date": types.Schema(
                    type=types.Type.STRING,
                    description="End date in YYYY-MM-DD format (inclusive)",
                ),
                "status": types.Schema(
                    type=types.Type.STRING,
                    description="Filter by status. Only use if user explicitly asks.",
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="top_customers",
        description="Get top customers ranked by total spending (sum of total_inr). All statuses included by default. Returns ties if they exist.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "limit": types.Schema(
                    type=types.Type.INTEGER,
                    description="Number of top customers to return (default 5)",
                ),
                "category": types.Schema(
                    type=types.Type.STRING,
                    description="Filter by category",
                ),
                "status": types.Schema(
                    type=types.Type.STRING,
                    description="Filter by status. Only use if user explicitly asks.",
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="orders_by_date_range",
        description="Get orders within a date range. Use for time-based queries like 'orders in August' (start_date=2026-08-01, end_date=2026-08-31).",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "start_date": types.Schema(
                    type=types.Type.STRING,
                    description="Start date in YYYY-MM-DD format (inclusive)",
                ),
                "end_date": types.Schema(
                    type=types.Type.STRING,
                    description="End date in YYYY-MM-DD format (inclusive)",
                ),
                "category": types.Schema(
                    type=types.Type.STRING,
                    description="Filter by category",
                ),
                "city": types.Schema(
                    type=types.Type.STRING,
                    description="Filter by city",
                ),
                "status": types.Schema(
                    type=types.Type.STRING,
                    description="Filter by status",
                ),
            },
            required=["start_date", "end_date"],
        ),
    ),
    types.FunctionDeclaration(
        name="orders_by_customer",
        description="Get all orders for a specific customer by name.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "customer_name": types.Schema(
                    type=types.Type.STRING,
                    description="Customer name to look up",
                ),
            },
            required=["customer_name"],
        ),
    ),
    types.FunctionDeclaration(
        name="orders_by_city",
        description="Get all orders from a specific city.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "city": types.Schema(
                    type=types.Type.STRING,
                    description="City name to filter by",
                ),
            },
            required=["city"],
        ),
    ),
    types.FunctionDeclaration(
        name="orders_by_category",
        description="Get all orders in a specific product category.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "category": types.Schema(
                    type=types.Type.STRING,
                    description="Category name (Electronics/Accessories/Stationery/Furniture)",
                ),
            },
            required=["category"],
        ),
    ),
    types.FunctionDeclaration(
        name="summary_stats",
        description="Get overall summary statistics: total orders, revenue, unique customers, status/category/city breakdowns, date range.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={},
        ),
    ),
]


def _create_client() -> genai.Client:
    """Create and return a Gemini client."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY not set. Add it to your .env file."
        )
    return genai.Client(api_key=GEMINI_API_KEY)


def _execute_tool(name: str, args: dict) -> dict:
    """Execute a tool by name with validated arguments."""
    if name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool: {name}"}

    tool_fn = TOOL_REGISTRY[name]
    try:
        result = tool_fn(**args)
        return result
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return {"error": f"Tool '{name}' failed: {str(e)}"}


async def chat(user_message: str) -> dict[str, Any]:
    """
    Process a user message through the Gemini function-calling loop.
    Returns {"reply": str, "tool_used": str | None}
    """
    client = _create_client()

    tools = types.Tool(function_declarations=TOOL_DECLARATIONS)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[tools],
        temperature=0.1,
    )

    # Build initial contents
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)],
        )
    ]

    tool_used = None

    for iteration in range(MAX_TOOL_ITERATIONS):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=config,
            )
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {
                "reply": "I'm sorry, I encountered an error connecting to the AI service. Please try again.",
                "tool_used": None,
            }

        # Check if the model wants to call a function
        candidate = response.candidates[0] if response.candidates else None
        if not candidate or not candidate.content or not candidate.content.parts:
            return {
                "reply": "I'm sorry, I couldn't generate a response. Please try rephrasing your question.",
                "tool_used": tool_used,
            }

        parts = candidate.content.parts

        # Check for function calls
        function_calls = [p for p in parts if p.function_call]

        if not function_calls:
            # Model returned text — we're done
            text_parts = [p.text for p in parts if p.text]
            reply = "\n".join(text_parts) if text_parts else "I couldn't generate a response."
            return {"reply": reply, "tool_used": tool_used}

        # Execute each function call
        contents.append(candidate.content)

        function_response_parts = []
        for fc_part in function_calls:
            fc = fc_part.function_call
            tool_name = fc.name
            tool_args = dict(fc.args) if fc.args else {}

            logger.info(f"Tool call: {tool_name}({tool_args})")
            tool_used = tool_name

            result = _execute_tool(tool_name, tool_args)

            function_response_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response=result,
                )
            )

        contents.append(
            types.Content(
                role="tool",
                parts=function_response_parts,
            )
        )

    # Hit max iterations
    return {
        "reply": "I'm sorry, I wasn't able to complete your request within the allowed number of steps. Please try simplifying your question.",
        "tool_used": tool_used,
    }
