"""
Milo Agent — Gemini function calling with tool execution loop.
Uses the official google-genai SDK with native function calling.
"""

import logging
from typing import Any
from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_MODEL, MAX_TOOL_ITERATIONS
from .tools import dispatch_tool, GEMINI_FUNCTION_DECLARATIONS

logger = logging.getLogger("milo.agent")

# ──────────────────────────── System Prompt ────────────────────────────

SYSTEM_PROMPT = """You are Milo, an AI assistant for order intelligence. You help users answer questions about orders.csv.

IMPORTANT RULES:
1. You MUST use the provided tools (lookup_order or analyze_orders) to answer questions about orders. NEVER invent order data or do math yourself.
2. Routing rules:
   - Specific order ID (e.g. 'ORD-1025') -> call lookup_order(order_id=...).
   - Counts, revenue, rankings, top customers, or filtered lists -> call analyze_orders(operation=...).
3. Revenue calculation:
   - When reporting revenue, state that it is the sum of total_inr across recorded orders.
   - All statuses (including cancelled/returned) are included by default unless the user explicitly asks for a status filter.
4. Top customer:
   - Groups by customer_name and sums total_inr. All statuses are included unless filtered. Always report any ties.
5. Date interpretation:
   - 'August' means August 2026 (2026-08-01 to 2026-08-31). The dataset spans June 2026 to September 2026.
6. Display currency in Indian format with ₹ (e.g., ₹1,12,282).
7. If a tool reports that an order was not found or no matches were found, state that clearly and truthfully. Never invent placeholder records.
8. Be concise, professional, and clear.
"""


def _create_client() -> genai.Client:
    """Create and return a Gemini client."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set. Add it to your .env file.")
    return genai.Client(api_key=GEMINI_API_KEY)


async def chat(user_message: str) -> dict[str, Any]:
    """Process a user message through the Gemini function-calling loop.
    Returns {"reply": str, "tool_used": str | None}
    """
    client = _create_client()

    tools = types.Tool(function_declarations=GEMINI_FUNCTION_DECLARATIONS)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[tools],
        temperature=0.1,
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)],
        )
    ]

    tool_used = None

    for _iteration in range(MAX_TOOL_ITERATIONS):
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

        candidate = response.candidates[0] if response.candidates else None
        if not candidate or not candidate.content or not candidate.content.parts:
            return {
                "reply": "I'm sorry, I couldn't generate a response. Please try rephrasing your question.",
                "tool_used": tool_used,
            }

        parts = candidate.content.parts
        function_calls = [p for p in parts if p.function_call]

        if not function_calls:
            text_parts = [p.text for p in parts if p.text]
            reply = "\n".join(text_parts) if text_parts else "I couldn't generate a response."
            return {"reply": reply, "tool_used": tool_used}

        contents.append(candidate.content)

        function_response_parts = []
        for fc_part in function_calls:
            fc = fc_part.function_call
            t_name = fc.name
            t_args = dict(fc.args) if fc.args else {}

            logger.info(f"Tool call: {t_name}({t_args})")
            tool_used = t_name

            result = dispatch_tool(t_name, t_args)

            function_response_parts.append(
                types.Part.from_function_response(
                    name=t_name,
                    response=result,
                )
            )

        contents.append(
            types.Content(
                role="tool",
                parts=function_response_parts,
            )
        )

    return {
        "reply": "I'm sorry, I wasn't able to complete your request within the allowed number of steps.",
        "tool_used": tool_used,
    }
