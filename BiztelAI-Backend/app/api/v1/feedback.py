"""Feedback submission endpoint for RAG quality monitoring."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from pydantic import ValidationError as PydanticValidationError
from app.api.deps import get_current_user
from app.constants import AuditAction
from app.schemas.llm import FeedbackCreateRequest
from app.services.audit_service import AuditService
from app.services.feedback_service import FeedbackService
from app.utils.errors import ValidationError

feedback_bp = Blueprint("feedback", __name__)
feedback_service = FeedbackService()


@feedback_bp.route("/feedback", methods=["POST"])
@jwt_required()
def submit_feedback():
    """Submit rating and qualitative feedback on Copilot answers."""
    user = get_current_user()
    raw = request.get_json() or {}

    try:
        req = FeedbackCreateRequest.model_validate(raw)
    except PydanticValidationError as e:
        raise ValidationError("Feedback validation failed.", details=e.errors())

    fb = feedback_service.submit_feedback(user_id=str(user.id), request_data=req)

    AuditService.log_event(
        action=AuditAction.FEEDBACK_SUBMIT.value,
        user_id=str(user.id),
        target_type="message",
        target_id=req.message_id,
        details={"rating": req.rating, "flagged": req.flag_for_review},
    )

    return jsonify({
        "success": True,
        "message": "Feedback submitted successfully.",
        "data": fb.model_dump(),
    }), 201

