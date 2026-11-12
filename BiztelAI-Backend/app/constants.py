"""Centralized constants and enums for BiztelAI Manufacturing SOP Copilot.

Includes role-based access, document and ingestion lifecycle states,
structured response block types, and query intents.
"""

from enum import Enum


class UserRole(str, Enum):
    """User access control roles."""
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    OPERATOR = "operator"
    AUDITOR = "auditor"


class DocumentStatus(str, Enum):
    """Document lifecycle states."""
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"


class IngestionStatus(str, Enum):
    """Asynchronous ingestion job states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BlockType(str, Enum):
    """Permitted UI block types for rich structured responses."""
    MARKDOWN = "markdown"
    STEPS = "steps"
    CHECKLIST = "checklist"
    CALLOUT = "callout"
    TABLE = "table"
    MERMAID = "mermaid"
    IMAGE = "image"
    SOURCE = "source"
    QUOTE = "quote"
    COMPARISON = "comparison"
    ACCORDION = "accordion"
    PROGRESS = "progress"


class CalloutVariant(str, Enum):
    """Callout visual semantics."""
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    SUCCESS = "success"
    NOTE = "note"


class QuestionIntent(str, Enum):
    """Intent classification for incoming queries."""
    NORMAL = "normal"
    PROCEDURAL = "procedural"
    SAFETY_CRITICAL = "safety_critical"
    COMPARISON = "comparison"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"
    UNANSWERABLE = "unanswerable"


class StepCompletionStatus(str, Enum):
    """Guided procedure step completion tracking."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class AuditAction(str, Enum):
    """Audit log action codes."""
    AUTH_LOGIN = "auth.login"
    AUTH_REGISTER = "auth.register"
    AUTH_REFRESH = "auth.refresh"
    AUTH_LOGOUT = "auth.logout"
    DOC_UPLOAD = "document.upload"
    DOC_DELETE = "document.delete"
    DOC_REPROCESS = "document.reprocess"
    CHAT_QUERY = "chat.query"
    PROCEDURE_GENERATE = "procedure.generate"
    PROCEDURE_PROGRESS = "procedure.progress"
    FEEDBACK_SUBMIT = "feedback.submit"
    ADMIN_CONFIG_UPDATE = "admin.config_update"

