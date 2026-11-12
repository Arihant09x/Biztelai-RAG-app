"""Guided Procedure Generation and Step Progress Persistence endpoints."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from pydantic import ValidationError as PydanticValidationError
from app.api.deps import get_current_user
from app.constants import AuditAction
from app.schemas.procedure import ProcedureGenerateRequest, ProcedureProgressUpdateRequest
from app.services.audit_service import AuditService
from app.services.procedure_service import ProcedureService
from app.utils.errors import ValidationError

procedures_bp = Blueprint("procedures", __name__)
procedure_service = ProcedureService()


@procedures_bp.route("/procedures/generate", methods=["POST"])
@jwt_required()
def generate_procedure():
    """Extract and generate a source-grounded guided procedure for machinery or SOP operations."""
    user = get_current_user()
    raw_data = request.get_json() or {}

    try:
        req = ProcedureGenerateRequest.model_validate(raw_data)
    except PydanticValidationError as e:
        raise ValidationError("Procedure generation validation failed.", details=e.errors())

    proc_res = procedure_service.generate_guided_procedure(
        user_id=str(user.id),
        query=req.query,
        document_id=req.document_id,
        department=req.department,
        conversation_id=req.conversation_id,
    )

    AuditService.log_event(
        action=AuditAction.PROCEDURE_GENERATE.value,
        user_id=str(user.id),
        target_type="procedure",
        target_id=proc_res.id,
        details={"query": req.query, "steps_count": len(proc_res.steps)},
    )

    return jsonify({
        "success": True,
        "data": proc_res.model_dump(),
    }), 201


@procedures_bp.route("/procedures/<procedure_id>/progress", methods=["POST"])
@jwt_required()
def update_progress(procedure_id: str):
    """Update checkbox state, execution status, and supervisor notes for a specific procedure step."""
    user = get_current_user()
    raw_data = request.get_json() or {}

    try:
        req = ProcedureProgressUpdateRequest.model_validate(raw_data)
    except PydanticValidationError as e:
        raise ValidationError("Progress update validation failed.", details=e.errors())

    step_res = procedure_service.update_step_progress(
        procedure_id=procedure_id,
        user_id=str(user.id),
        update_data=req,
    )

    AuditService.log_event(
        action=AuditAction.PROCEDURE_PROGRESS.value,
        user_id=str(user.id),
        target_type="procedure",
        target_id=procedure_id,
        details={"step_id": req.step_id, "status": req.status},
    )

    return jsonify({
        "success": True,
        "message": f"Step '{req.step_id}' updated to '{req.status}'.",
        "data": step_res.model_dump(),
    }), 200

