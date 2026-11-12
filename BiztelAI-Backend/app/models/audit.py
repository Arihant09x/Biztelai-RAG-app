"""Security and compliance audit trail models."""

from sqlalchemy import Column, ForeignKey, JSON, String
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.base import BaseModel, GUID


class AuditLog(BaseModel):
    """Immutable audit record for regulatory traceability and SOC2/ISO compliance."""
    __tablename__ = "audit_logs"

    user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    target_type = Column(String(50), nullable=True)  # e.g., 'document', 'conversation', 'user'
    target_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details = Column(JSON, default=dict, nullable=False)

    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} user={self.user_id}>"

