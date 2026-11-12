"""Chat and conversation request and response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.response_blocks import CopilotAnswerResponse, SourceCitation


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChatQueryRequest(StrictSchema):
    question: str = Field(min_length=2, max_length=2000, description="Supervisor or operator question")
    conversation_id: Optional[str] = None
    department: Optional[str] = None
    category: Optional[str] = None
    document_ids: Optional[List[str]] = None
    stream: bool = False


class ConversationCreateRequest(StrictSchema):
    title: Optional[str] = Field(default="New SOP Discussion", max_length=255)
    department_filter: Optional[str] = None
    category_filter: Optional[str] = None


class MessageResponse(BaseModel):
    id: Union[str, UUID]
    sender_type: str
    content: str
    structured_response: Dict[str, Any] = Field(default_factory=dict)
    sources: List[SourceCitation] = Field(default_factory=list)
    intent: Optional[str] = None
    latency_ms: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: Union[str, UUID]
    title: str
    department_filter: Optional[str] = None
    category_filter: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = Field(default_factory=list)
