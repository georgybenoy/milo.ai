"""
Pydantic schemas for API request/response and tool arguments.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


# --- API Schemas ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    orders_loaded: int
    model: str


# --- Tool Argument Schemas ---

class LookupOrderArgs(BaseModel):
    order_id: str = Field(..., min_length=1, max_length=32)


class AnalyzeOrdersArgs(BaseModel):
    operation: Literal["count_orders", "sum_revenue", "top_customer", "list_orders"]
    status: Optional[str] = None
    category: Optional[str] = None
    customer_name: Optional[str] = None
    city: Optional[str] = None
    product: Optional[str] = None
    payment_method: Optional[str] = None
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
