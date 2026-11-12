"""RAG Evaluation framework database entities for benchmark tracking."""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.base import BaseModel, GUID


class EvaluationRun(BaseModel):
    """Execution run summary of the RAG evaluation framework."""
    __tablename__ = "evaluation_runs"

    run_name = Column(String(100), nullable=False)
    dataset_name = Column(String(100), nullable=False)
    total_queries = Column(Integer, default=0, nullable=False)
    passed_queries = Column(Integer, default=0, nullable=False)
    metrics_summary = Column(JSON, default=dict, nullable=False)
    created_by_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    creator = relationship("User")
    items = relationship("EvaluationItem", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<EvaluationRun {self.run_name} total={self.total_queries}>"


class EvaluationItem(BaseModel):
    """Detailed query-level evaluation score and grounding result."""
    __tablename__ = "evaluation_items"

    evaluation_run_id = Column(GUID, ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)
    expected_answerable = Column(Boolean, nullable=False)
    actual_answerable = Column(Boolean, nullable=False)

    precision = Column(Float, default=0.0, nullable=False)
    recall = Column(Float, default=0.0, nullable=False)
    groundedness = Column(Float, default=0.0, nullable=False)
    citation_correctness = Column(Float, default=0.0, nullable=False)
    latency_ms = Column(Float, default=0.0, nullable=False)
    passed = Column(Boolean, default=False, nullable=False, index=True)

    details = Column(JSON, default=dict, nullable=False)

    run = relationship("EvaluationRun", back_populates="items")

