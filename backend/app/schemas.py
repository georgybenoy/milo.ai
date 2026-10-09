"""
Pydantic schemas for API request/response, health, dataset info, and tool arguments.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


# --- API Schemas ---

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Message must be a string.")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or whitespace only.")
        if len(stripped) > 2000:
            raise ValueError("Message cannot exceed 2000 characters.")
        return stripped


class ChatResponse(BaseModel):
    reply: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    data_loaded: bool
    ai_configured: bool


class DatasetInfo(BaseModel):
    record_count: int
    start_date: str
    end_date: str


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
