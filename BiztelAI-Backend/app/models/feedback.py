"""Feedback model for tracking user ratings and review flags on Copilot answers."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.base import BaseModel, GUID


class Feedback(BaseModel):
    """Stores supervisor / operator ratings and qualitative feedback on RAG answers."""
    __tablename__ = "feedback"

    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(GUID, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    rating = Column(Integer, nullable=False)  # 1 (positive) or -1 (negative), or 1 to 5 scale
    comment = Column(Text, nullable=True)
    is_flagged_for_review = Column(Boolean, default=False, nullable=False, index=True)

    user = relationship("User")
    message = relationship("Message", back_populates="feedback")

    def __repr__(self) -> str:
        return f"<Feedback msg={self.message_id} rating={self.rating}>"

