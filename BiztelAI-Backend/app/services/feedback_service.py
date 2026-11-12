"""Feedback capture service for continuous evaluation and QA flagging."""

from app.extensions import db
from app.models.conversation import Message
from app.models.feedback import Feedback
from app.schemas.llm import FeedbackCreateRequest, FeedbackResponse
from app.utils.errors import ConflictError, NotFoundError
import structlog

logger = structlog.get_logger(__name__)


class FeedbackService:
    """Records supervisor / operator ratings and qualitative feedback on RAG answers."""

    def submit_feedback(self, user_id: str, request_data: FeedbackCreateRequest) -> FeedbackResponse:
        """Record rating for an assistant message."""
        # 1. Verify message exists
        msg = Message.query.get(request_data.message_id)
        if not msg:
            raise NotFoundError(f"Message '{request_data.message_id}' not found.")

        # 2. Check if feedback already submitted for this message
        existing = Feedback.query.filter_by(message_id=request_data.message_id).first()
        if existing:
            # Update rating
            existing.rating = request_data.rating
            if request_data.comment is not None:
                existing.comment = request_data.comment
            existing.is_flagged_for_review = request_data.flag_for_review
            db.session.commit()
            return FeedbackResponse(
                id=str(existing.id),
                message_id=str(existing.message_id),
                rating=existing.rating,
                comment=existing.comment,
                is_flagged_for_review=existing.is_flagged_for_review,
                created_at=existing.created_at,
            )

        new_fb = Feedback(
            user_id=user_id,
            message_id=request_data.message_id,
            rating=request_data.rating,
            comment=request_data.comment,
            is_flagged_for_review=request_data.flag_for_review,
        )
        db.session.add(new_fb)
        db.session.commit()

        logger.info("feedback_submitted", message_id=request_data.message_id, rating=request_data.rating, user_id=user_id)
        return FeedbackResponse(
            id=str(new_fb.id),
            message_id=str(new_fb.message_id),
            rating=new_fb.rating,
            comment=new_fb.comment,
            is_flagged_for_review=new_fb.is_flagged_for_review,
            created_at=new_fb.created_at,
        )

