"""Guided Procedure generation and progress tracking schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProcedureGenerateRequest(StrictSchema):
    query: str = Field(min_length=3, max_length=1000, description="Procedure query e.g. How to inspect CNC spindle bearings")
    document_id: Optional[str] = None
    department: Optional[str] = None
    conversation_id: Optional[str] = None


class ProcedureStepResponse(BaseModel):
    step_index: int
    step_id: str
    description: str
    status: str
    source_ids: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProcedureResponse(BaseModel):
    id: str
    title: str
    purpose: str
    prerequisites: List[str] = Field(default_factory=list)
    required_equipment: List[str] = Field(default_factory=list)
    status: str
    steps: List[ProcedureStepResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcedureProgressUpdateRequest(StrictSchema):
    step_id: str
    status: str = Field(description="pending, in_progress, completed, skipped, blocked")
    notes: Optional[str] = None

