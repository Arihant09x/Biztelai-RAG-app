"""Feedback, Admin metrics, and LLM diagnostic request and response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


# Feedback Schemas
class FeedbackCreateRequest(StrictSchema):
    message_id: str
    rating: int = Field(description="Rating score (1 for thumbs up, -1 for thumbs down)")
    comment: Optional[str] = Field(default=None, max_length=1000)
    flag_for_review: bool = False


class FeedbackResponse(BaseModel):
    id: str
    message_id: str
    rating: int
    comment: Optional[str] = None
    is_flagged_for_review: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Admin Metrics Schemas
class AdminMetricsResponse(BaseModel):
    total_documents: int
    indexed_documents: int
    total_pages: int
    total_chunks: int
    total_users: int
    total_queries: int
    average_latency_ms: float
    positive_feedback_rate: float


# LLM Diagnostic Schemas
class LLMStatusResponse(BaseModel):
    configured_provider: str
    api_base_url: str
    model_name: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    status: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class LLMTestConnectionRequest(StrictSchema):
    prompt: Optional[str] = "Hello BiztelAI Copilot. Confirm connection in 5 words."


class LLMTestConnectionResponse(BaseModel):
    success: bool
    provider_endpoint: str
    model: str
    response_text: Optional[str] = None
    latency_ms: float
    error_message: Optional[str] = None

