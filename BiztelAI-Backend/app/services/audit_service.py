"""Audit logging service capturing security, compliance, and document access events."""

from typing import Any, Dict, Optional
from flask import request
from app.extensions import db
from app.models.audit import AuditLog
import structlog

logger = structlog.get_logger(__name__)


class AuditService:
    """Records immutable audit trail entries."""

    @staticmethod
    def log_event(
        action: str,
        user_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Create audit log entry with client IP and user agent."""
        ip_addr = None
        user_agent = None
        try:
            if request:
                ip_addr = request.remote_addr
                user_agent = request.headers.get("User-Agent")
        except RuntimeError:
            pass

        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            ip_address=ip_addr,
            user_agent=user_agent,
            details=details or {},
        )
        db.session.add(audit_entry)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("audit_logging_failed", error=str(e), action=action)

        return audit_entry

