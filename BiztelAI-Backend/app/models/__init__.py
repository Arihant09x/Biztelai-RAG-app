"""Models registry exporting all SQLAlchemy entities."""

from app.models.base import BaseModel, GUID, VectorType
from app.models.user import User, Role, Permission, role_permissions
from app.models.document import Document, DocumentVersion, DocumentPage, DocumentChunk, DocumentAsset
from app.models.ingestion import IngestionJob
from app.models.conversation import Conversation, Message, MessageSource
from app.models.procedure import ProcedureExecution, ProcedureStepProgress
from app.models.feedback import Feedback
from app.models.audit import AuditLog
from app.models.evaluation import EvaluationRun, EvaluationItem
from app.models.index import EmbeddingModel, IndexVersion

__all__ = [
    "BaseModel",
    "GUID",
    "VectorType",
    "User",
    "Role",
    "Permission",
    "role_permissions",
    "Document",
    "DocumentVersion",
    "DocumentPage",
    "DocumentChunk",
    "DocumentAsset",
    "IngestionJob",
    "Conversation",
    "Message",
    "MessageSource",
    "ProcedureExecution",
    "ProcedureStepProgress",
    "Feedback",
    "AuditLog",
    "EvaluationRun",
    "EvaluationItem",
    "EmbeddingModel",
    "IndexVersion",
]

