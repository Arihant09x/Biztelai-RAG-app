"""IngestionJob model for tracking asynchronous PDF extraction and indexing."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.base import BaseModel, GUID
from app.constants import IngestionStatus


class IngestionJob(BaseModel):
    """Tracks asynchronous Celery background ingestion status and progress."""
    __tablename__ = "ingestion_jobs"

    document_id = Column(GUID, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), default=IngestionStatus.PENDING.value, nullable=False, index=True)
    progress_percent = Column(Integer, default=0, nullable=False)
    current_stage = Column(String(100), default="queued", nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    celery_task_id = Column(String(100), nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    document = relationship("Document", back_populates="ingestion_jobs")

    def __repr__(self) -> str:
        return f"<IngestionJob id={self.id} doc={self.document_id} status={self.status} progress={self.progress_percent}%>"

