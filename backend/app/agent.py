"""
Milo Agent — Gemini function calling with native tool execution loop.
Uses the official google-genai SDK with native function calling.
Model client is mockable/injectable for unit testing without network.
"""

import logging
from typing import Any
from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_MODEL, MAX_TOOL_ITERATIONS
from .tools import dispatch_tool, GEMINI_FUNCTION_DECLARATIONS

logger = logging.getLogger("milo.agent")


# ──────────────────────────── Custom Exceptions ────────────────────────────


class MiloAgentError(Exception):
    """Base exception for all Milo agent errors."""
    pass


class MiloProviderError(MiloAgentError):
    """Raised for AI provider errors (network, timeout, rate-limit, quota, outages)."""
    pass


class MiloSafetyError(MiloAgentError):
    """Raised when the prompt or response is blocked by safety filters."""
    pass


class MiloIterationLimitError(MiloAgentError):
    """Raised when agent exceeds MAX_TOOL_ITERATIONS without reaching a final response."""
    pass


class MiloClientError(MiloAgentError):
    """Raised when request arguments are invalid or client is misconfigured."""
    pass


# ──────────────────────────── System Instruction ────────────────────────────

SYSTEM_INSTRUCTION = """You are Milo, an AI assistant for order intelligence on orders.csv.

BEHAVIOR AND TONE:
1. Be calm, concise, and precise.
2. Answer ONLY using the facts returned by tool results. Never invent, hallucinate, or assume order data or do math yourself.
3. If a question is unanswerable from the data or out of scope, state clearly that you cannot answer it from the available dataset.
4. Never claim to perform modifying actions (you cannot refund, cancel, edit, or place orders; you are strictly a read-only analytical assistant).
5. Report missing data explicitly (e.g. if an order ID is not found, state that it was not found; never invent a placeholder).
6. When calculating or reporting revenue:
   - State clearly that revenue is the sum of total_inr for recorded orders.
   - Mention that it includes all statuses (including cancelled and returned orders) unless a specific status filter was applied.
7. Format all monetary amounts in Indian grouping with the ₹ symbol (e.g. ₹1,12,282).
8. Always name the period and any filters used (e.g. 'for August 2026', 'for Electronics category', 'with Delivered status').
9. Structure answers with short paragraphs and clean bullet points for readability.

ROUTING RULES:
- Specific order ID (e.g. 'ORD-1025') -> lookup_order(order_id='ORD-1025').
- Counts, sums, revenue, customer rankings, or filtered order lists -> analyze_orders(operation=...).
  * operation='count_orders' counts rows (transactions), not sum of quantities.
  * operation='sum_revenue' calculates total revenue in INR.
  * operation='top_customer' identifies the top spending customer (grouping by customer, handling ties).
  * operation='list_orders' lists matching orders (capped at 25).
"""


def _create_client() -> genai.Client:
    """Create and return a production Gemini client."""
    if not GEMINI_API_KEY:
        raise MiloClientError("GEMINI_API_KEY is not set. Please configure it in your .env file.")
    return genai.Client(api_key=GEMINI_API_KEY)


async def chat(
    user_message: str,
    client: genai.Client | Any | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Execute the Gemini native function-calling loop for a user message.

    Supports dependency injection of `client` for network-free unit tests.
    Returns:
        {
            "reply": str,
            "tool_used": str | None,
            "tool_calls_history": list[dict],
        }
    """
    if not user_message or not user_message.strip():
        raise MiloClientError("Message must be a non-empty string.")

    active_client = client if client is not None else _create_client()
    active_model = model or GEMINI_MODEL

    tools = types.Tool(function_declarations=GEMINI_FUNCTION_DECLARATIONS)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[tools],
        temperature=0.1,
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message.strip())],
        )
    ]

    tool_used: str | None = None
    tool_calls_history: list[dict[str, Any]] = []

    for iteration in range(MAX_TOOL_ITERATIONS):
        try:
            response = active_client.models.generate_content(
                model=active_model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            err_msg = str(exc)
            logger.error(f"Gemini API provider error during iteration {iteration}: {exc}")
            if "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower() or "429" in err_msg:
                raise MiloProviderError("Gemini quota or rate limit exceeded. Please try again later.") from exc
            if "safety" in err_msg.lower() or "blocked" in err_msg.lower():
                raise MiloSafetyError("The prompt was blocked by safety filters.") from exc
            raise MiloProviderError(f"Gemini provider error: {exc}") from exc

        # Check response structure
        candidate = response.candidates[0] if getattr(response, "candidates", None) else None
        if not candidate:
            raise MiloProviderError("Received an empty response from the AI model.")

        finish_reason = str(getattr(candidate, "finish_reason", ""))
        if "SAFETY" in finish_reason:
            raise MiloSafetyError("Response blocked by AI provider safety filters.")

        if not getattr(candidate, "content", None) or not candidate.content.parts:
            raise MiloProviderError("Received an empty or invalid response from the AI model.")

        parts = candidate.content.parts
        function_calls = [p for p in parts if getattr(p, "function_call", None)]

        # If no function calls, we have reached the final text answer
        if not function_calls:
            text_parts = [p.text for p in parts if getattr(p, "text", None)]
            reply = "\n".join(text_parts).strip() if text_parts else "I am sorry, no text response could be generated."
            return {
                "reply": reply,
                "tool_used": tool_used,
                "tool_calls_history": tool_calls_history,
            }

        # Model requests tool call(s) — append model turn to contents
        contents.append(candidate.content)

        function_response_parts = []
        for fc_part in function_calls:
            fc = fc_part.function_call
            t_name = fc.name
            t_args = dict(fc.args) if getattr(fc, "args", None) else {}

            logger.info(f"Dispatching tool: {t_name} with args: {t_args}")
            tool_used = t_name
            tool_calls_history.append({"tool": t_name, "args": t_args})

            # Deterministic dispatch (catches errors and returns structured error dict)
            tool_result = dispatch_tool(t_name, t_args)

            # Pass result (or structured error) back to model
            function_response_parts.append(
                types.Part.from_function_response(
                    name=t_name,
                    response=tool_result,
                )
            )

        # Append tool response turn to conversation contents (Google GenAI API expects role='user' for function responses)
        contents.append(
            types.Content(
                role="user",
                parts=function_response_parts,
            )
        )

    # Reached MAX_TOOL_ITERATIONS without terminating text
    raise MiloIterationLimitError(
        f"Exceeded maximum tool iterations ({MAX_TOOL_ITERATIONS}) without completing request."
    )
