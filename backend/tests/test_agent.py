"""
Unit tests for the Milo Gemini agent loop with mock client.
Tests tool dispatching, multi-turn flows, error handling, safety, and iteration limits without network calls.
"""

from typing import Any
import pytest
from google.genai import types

from app.agent import (
    chat,
    MiloClientError,
    MiloProviderError,
    MiloSafetyError,
    MiloIterationLimitError,
)
from app.data_loader import load_orders
from app.config import CSV_PATH


@pytest.fixture(autouse=True, scope="module")
def init_data():
    load_orders(CSV_PATH)


class MockGenAIClient:
    """Mock Gemini client that replays predetermined responses or raises exceptions."""

    def __init__(self, responses: list[Any]):
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []
        self.models = self

    def generate_content(self, model: str, contents: list, config: Any):
        self.calls.append({"model": model, "contents": list(contents), "config": config})
        if not self.responses:
            raise RuntimeError("MockGenAIClient ran out of mock responses.")
        next_resp = self.responses.pop(0)
        if isinstance(next_resp, Exception):
            raise next_resp
        return next_resp


def make_text_response(text: str) -> types.GenerateContentResponse:
    part = types.Part.from_text(text=text)
    content = types.Content(role="model", parts=[part])
    candidate = types.Candidate(content=content)
    return types.GenerateContentResponse(candidates=[candidate])


def make_function_call_response(calls: list[tuple[str, dict]]) -> types.GenerateContentResponse:
    parts = []
    for name, args in calls:
        fc = types.FunctionCall(name=name, args=args)
        parts.append(types.Part(function_call=fc))
    content = types.Content(role="model", parts=parts)
    candidate = types.Candidate(content=content)
    return types.GenerateContentResponse(candidates=[candidate])


# ──────────────────────────── Test Cases ────────────────────────────


@pytest.mark.asyncio
async def test_tool_dispatched_and_final_text_produced():
    """Verify tool call is dispatched, result returned to model, and final text produced."""
    mock_client = MockGenAIClient([
        make_function_call_response([("lookup_order", {"order_id": "ORD-1025"})]),
        make_text_response("Order ORD-1025 was placed by Karthik Rao for ₹2,397 on 2026-07-14."),
    ])

    result = await chat("Check order ORD-1025", client=mock_client)

    assert result["tool_used"] == "lookup_order"
    assert "Karthik Rao" in result["reply"]
    assert len(mock_client.calls) == 2

    # Verify conversation history passed in turn 2 contained the tool response
    turn_2_contents = mock_client.calls[1]["contents"]
    assert len(turn_2_contents) == 3
    assert turn_2_contents[0].role == "user"
    assert turn_2_contents[1].role == "model"
    assert turn_2_contents[2].role == "user"


@pytest.mark.asyncio
async def test_multiple_tool_calls_parallel():
    """Verify multiple parallel tool calls in a single model turn are all dispatched."""
    mock_client = MockGenAIClient([
        make_function_call_response([
            ("lookup_order", {"order_id": "ORD-1025"}),
            ("lookup_order", {"order_id": "ORD-1026"}),
        ]),
        make_text_response("Found both orders ORD-1025 and ORD-1026."),
    ])

    result = await chat("Compare ORD-1025 and ORD-1026", client=mock_client)

    assert len(result["tool_calls_history"]) == 2
    assert result["tool_calls_history"][0]["args"]["order_id"] == "ORD-1025"
    assert result["tool_calls_history"][1]["args"]["order_id"] == "ORD-1026"
    assert "Found both" in result["reply"]


@pytest.mark.asyncio
async def test_multiple_tool_calls_sequential():
    """Verify sequential tool calls across multiple iterations."""
    mock_client = MockGenAIClient([
        make_function_call_response([("analyze_orders", {"operation": "top_customer"})]),
        make_function_call_response([("analyze_orders", {"operation": "list_orders", "customer_name": "Rohan Das"})]),
        make_text_response("The top customer is Rohan Das with total spend ₹1,12,282."),
    ])

    result = await chat("Who is top customer and list their orders?", client=mock_client)

    assert len(mock_client.calls) == 3
    assert len(result["tool_calls_history"]) == 2
    assert result["tool_calls_history"][0]["args"]["operation"] == "top_customer"
    assert result["tool_calls_history"][1]["args"]["customer_name"] == "Rohan Das"
    assert "Rohan Das" in result["reply"]


@pytest.mark.asyncio
async def test_invalid_args_passed_to_model():
    """Verify invalid tool arguments are safely passed back to model as structured error."""
    mock_client = MockGenAIClient([
        make_function_call_response([("analyze_orders", {"operation": "fly_to_mars"})]),
        make_text_response("I apologize, but that operation is invalid."),
    ])

    result = await chat("Fly to mars", client=mock_client)

    assert "invalid" in result["reply"].lower()
    tool_content = mock_client.calls[1]["contents"][2]
    # Check that the tool response received by model contained error details
    tool_resp = tool_content.parts[0].function_response.response
    assert tool_resp["success"] is False
    assert "unknown operation" in tool_resp["error"].lower()


@pytest.mark.asyncio
async def test_missing_order_handled_truthfully():
    """Verify missing order is returned with found: False and handled truthfully."""
    mock_client = MockGenAIClient([
        make_function_call_response([("lookup_order", {"order_id": "ORD-9999"})]),
        make_text_response("Order ORD-9999 was not found in the dataset."),
    ])

    result = await chat("Where is ORD-9999?", client=mock_client)

    assert "not found" in result["reply"].lower()
    tool_content = mock_client.calls[1]["contents"][2]
    tool_resp = tool_content.parts[0].function_response.response
    assert tool_resp["found"] is False


@pytest.mark.asyncio
async def test_iteration_limit_stops_runaway_loop():
    """Verify infinite tool calls are halted when MAX_TOOL_ITERATIONS is reached."""
    # Always return another tool call
    infinite_calls = [
        make_function_call_response([("lookup_order", {"order_id": "ORD-1025"})])
        for _ in range(10)
    ]
    mock_client = MockGenAIClient(infinite_calls)

    with pytest.raises(MiloIterationLimitError, match="maximum tool iterations"):
        await chat("Loop forever", client=mock_client)


@pytest.mark.asyncio
async def test_provider_quota_error_mapped():
    """Verify rate-limit/quota provider errors map to MiloProviderError."""
    mock_client = MockGenAIClient([
        Exception("429 RESOURCE_EXHAUSTED: Quota exceeded for model")
    ])

    with pytest.raises(MiloProviderError, match="quota or rate limit"):
        await chat("Hello", client=mock_client)


@pytest.mark.asyncio
async def test_safety_block_mapped():
    """Verify safety blocks map to MiloSafetyError."""
    part = types.Part.from_text(text="")
    content = types.Content(role="model", parts=[part])
    candidate = types.Candidate(content=content, finish_reason="SAFETY")
    safety_resp = types.GenerateContentResponse(candidates=[candidate])

    mock_client = MockGenAIClient([safety_resp])

    with pytest.raises(MiloSafetyError, match="safety filters"):
        await chat("Dangerous query", client=mock_client)


@pytest.mark.asyncio
async def test_empty_message_rejected():
    """Verify empty user message raises MiloClientError."""
    with pytest.raises(MiloClientError, match="non-empty string"):
        await chat("   ")
