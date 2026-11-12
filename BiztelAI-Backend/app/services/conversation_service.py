"""Conversation and dialogue history service with ownership security checks."""

from typing import Any, Dict, List, Optional, Tuple
from app.extensions import db
from app.models.conversation import Conversation, Message, MessageSource
from app.models.document import Document
from app.models.user import User
from app.schemas.chat import ConversationDetailResponse, ConversationResponse, MessageResponse
from app.schemas.response_blocks import SourceCitation
from app.utils.errors import AuthorizationError, NotFoundError
import structlog

logger = structlog.get_logger(__name__)


class ConversationService:
    """Manages thread lifecycles, user authorization checks, and grounded dialogue storage."""

    def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = "New SOP Discussion",
        department_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
    ) -> Conversation:
        """Initialize a new conversation thread."""
        conv = Conversation(
            user_id=user_id,
            title=title or "New SOP Discussion",
            department_filter=department_filter,
            category_filter=category_filter,
            is_archived=False,
        )
        db.session.add(conv)
        db.session.commit()
        logger.info("conversation_created", conversation_id=str(conv.id), user_id=user_id)
        return conv

    def get_conversation_authorized(self, conversation_id: str, user: User) -> Conversation:
        """Fetch conversation enforcing ownership or supervisor/admin privilege."""
        conv = Conversation.query.filter_by(id=conversation_id, is_archived=False).first()
        if not conv:
            raise NotFoundError(f"Conversation '{conversation_id}' not found.")

        # Authorization check: only owner or supervisor/admin can access
        if str(conv.user_id) != str(user.id) and not user.is_supervisor:
            raise AuthorizationError("Access denied: You do not own this conversation.")

        return conv

    def list_user_conversations(self, user_id: str, skip: int = 0, limit: int = 20) -> List[ConversationResponse]:
        """List active conversations for the given user."""
        convs = (
            Conversation.query.filter_by(user_id=user_id, is_archived=False)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        result = []
        for c in convs:
            msg_count = Message.query.filter_by(conversation_id=c.id).count()
            result.append(
                ConversationResponse(
                    id=str(c.id),
                    title=c.title,
                    department_filter=c.department_filter,
                    category_filter=c.category_filter,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    message_count=msg_count,
                )
            )
        return result

    def archive_conversation(self, conversation_id: str, user: User) -> bool:
        """Soft delete/archive conversation thread."""
        conv = self.get_conversation_authorized(conversation_id, user)
        conv.is_archived = True
        db.session.commit()
        return True

    def append_message_turn(
        self,
        conversation_id: str,
        user_query: str,
        assistant_content: str,
        structured_response: Dict[str, Any],
        sources: List[SourceCitation],
        token_usage: Dict[str, Any],
        latency_ms: float,
        intent: Optional[str] = None,
    ) -> Tuple[Message, Message]:
        """Record the user question and the verified assistant response turn with citations."""
        # 1. User Message
        user_msg = Message(
            conversation_id=conversation_id,
            sender_type="user",
            content=user_query,
            structured_response_json={},
            intent=intent,
            token_usage={},
            latency_ms=0.0,
        )
        db.session.add(user_msg)
        db.session.flush()

        # 2. Assistant Message
        assistant_msg = Message(
            conversation_id=conversation_id,
            sender_type="assistant",
            content=assistant_content,
            structured_response_json=structured_response,
            intent=intent,
            token_usage=token_usage,
            latency_ms=latency_ms,
        )
        db.session.add(assistant_msg)
        db.session.flush()

        # 3. Message Sources (citations)
        for s in sources:
            source_record = MessageSource(
                message_id=assistant_msg.id,
                chunk_id=None,
                document_id=s.document_id,
                citation_label=s.id,
                relevance_score=s.relevance_score,
                snippet=s.snippet,
                page_number=s.page_number,
            )
            db.session.add(source_record)

        db.session.commit()
        return user_msg, assistant_msg

