"""
Pydantic schemas for API request/response and tool arguments.
"""

from pydantic import BaseModel, Field
from typing import Optional


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


# --- Tool Argument Schemas (validated before execution) ---

class LookupOrderArgs(BaseModel):
    order_id: str = Field(..., pattern=r"^ORD-\d{4}$")


class OrdersByStatusArgs(BaseModel):
    status: str = Field(...)

    def validate_status(self) -> str:
        allowed = {"delivered", "cancelled", "returned", "processing", "shipped"}
        normalized = self.status.strip().casefold()
        if normalized not in allowed:
            raise ValueError(
                f"Invalid status '{self.status}'. "
                f"Allowed: {', '.join(sorted(allowed))}"
            )
        return normalized


class RevenueArgs(BaseModel):
    category: Optional[str] = None
    city: Optional[str] = None
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    status: Optional[str] = None


class TopCustomersArgs(BaseModel):
    limit: int = Field(default=5, ge=1, le=60)
    category: Optional[str] = None
    status: Optional[str] = None


class OrdersByDateRangeArgs(BaseModel):
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    category: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None


class OrdersByCustomerArgs(BaseModel):
    customer_name: str = Field(..., min_length=1)


class OrdersByCityArgs(BaseModel):
    city: str = Field(..., min_length=1)


class OrdersByCategoryArgs(BaseModel):
    category: str = Field(..., min_length=1)


class SummaryStatsArgs(BaseModel):
    """No arguments needed — returns overall summary."""
    pass
