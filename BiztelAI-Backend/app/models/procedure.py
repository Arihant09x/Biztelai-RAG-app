"""Guided Procedure Execution and Step-by-Step Progress Tracking Models."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.base import BaseModel, GUID
from app.constants import StepCompletionStatus


class ProcedureExecution(BaseModel):
    """Represents an active or completed guided procedure instance."""
    __tablename__ = "procedure_executions"

    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(GUID, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    purpose = Column(Text, nullable=False)
    prerequisites = Column(JSON, default=list, nullable=False)
    required_equipment = Column(JSON, default=list, nullable=False)
    status = Column(String(50), default="in_progress", nullable=False)  # in_progress, completed, aborted

    user = relationship("User")
    conversation = relationship("Conversation")
    steps = relationship("ProcedureStepProgress", back_populates="procedure", cascade="all, delete-orphan", order_by="ProcedureStepProgress.step_index")

    def __repr__(self) -> str:
        return f"<ProcedureExecution {self.title} status={self.status}>"


class ProcedureStepProgress(BaseModel):
    """Tracks state and notes for individual steps within a procedure."""
    __tablename__ = "procedure_step_progress"

    procedure_id = Column(GUID, ForeignKey("procedure_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False, index=True)
    step_id = Column(String(50), nullable=False)  # e.g., 'step_1'
    description = Column(Text, nullable=False)
    status = Column(String(50), default=StepCompletionStatus.PENDING.value, nullable=False)
    source_ids = Column(JSON, default=list, nullable=False)
    notes = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    procedure = relationship("ProcedureExecution", back_populates="steps")
    completed_by = relationship("User")

    def __repr__(self) -> str:
        return f"<ProcedureStep {self.step_id} status={self.status}>"

