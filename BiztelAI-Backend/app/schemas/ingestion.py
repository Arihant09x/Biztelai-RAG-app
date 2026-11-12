"""Ingestion job status and tracking schemas."""

from datetime import datetime
from typing import Optional, Union
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class IngestionJobResponse(BaseModel):
    id: Union[str, UUID]
    document_id: Union[str, UUID]
    status: str
    progress_percent: int
    current_stage: str
    error_message: Optional[str] = None
    retry_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
