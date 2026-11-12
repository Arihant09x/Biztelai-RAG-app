"""Administration, operational telemetry, metrics, and evaluation inspection endpoints."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from app.api.deps import admin_required, supervisor_required
from app.constants import DocumentStatus
from app.models.conversation import Message
from app.models.document import Document, DocumentChunk, DocumentPage
from app.models.evaluation import EvaluationRun
from app.models.feedback import Feedback
from app.models.user import User

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/metrics", methods=["GET"])
@jwt_required()
@supervisor_required
def get_system_metrics():
    """Retrieve operational telemetry and aggregate statistics."""
    total_docs = Document.query.filter_by(is_deleted=False).count()
    indexed_docs = Document.query.filter_by(is_deleted=False, status=DocumentStatus.INDEXED.value).count()
    total_pages = DocumentPage.query.count()
    total_chunks = DocumentChunk.query.filter_by(is_active=True).count()
    total_users = User.query.filter_by(is_active=True).count()
    total_queries = Message.query.filter_by(sender_type="user").count()

    # Latency avg
    avg_latency = (
        Message.query.with_entities(func.avg(Message.latency_ms))
        .filter(Message.sender_type == "assistant", Message.latency_ms.isnot(None))
        .scalar()
        or 0.0
    )

    # Feedback score
    total_feedback = Feedback.query.count()
    positive_feedback = Feedback.query.filter(Feedback.rating > 0).count()
    pos_rate = round((positive_feedback / total_feedback * 100), 1) if total_feedback > 0 else 100.0

    return jsonify({
        "success": True,
        "data": {
            "total_documents": total_docs,
            "indexed_documents": indexed_docs,
            "total_pages": total_pages,
            "total_chunks": total_chunks,
            "total_users": total_users,
            "total_queries": total_queries,
            "average_latency_ms": round(float(avg_latency), 2),
            "positive_feedback_rate_percent": pos_rate,
        },
    }), 200


@admin_bp.route("/admin/documents", methods=["GET"])
@jwt_required()
@admin_required
def list_admin_documents():
    """Retrieve complete administrative inventory of all documents including internal storage paths."""
    docs = Document.query.order_by(Document.created_at.desc()).all()
    results = []
    for d in docs:
        results.append({
            "id": str(d.id),
            "title": d.title,
            "original_filename": d.original_filename,
            "stored_filename": d.stored_filename,
            "sha256": d.sha256_hash,
            "file_size_bytes": d.file_size_bytes,
            "category": d.category,
            "department": d.department,
            "status": d.status,
            "is_deleted": d.is_deleted,
            "created_at": d.created_at,
        })
    return jsonify({
        "success": True,
        "data": results,
    }), 200


@admin_bp.route("/admin/evaluations", methods=["GET"])
@jwt_required()
@supervisor_required
def list_evaluations():
    """Retrieve historical RAG evaluation runs and grounding benchmark scores."""
    runs = EvaluationRun.query.order_by(EvaluationRun.created_at.desc()).limit(20).all()
    results = []
    for r in runs:
        results.append({
            "id": str(r.id),
            "run_name": r.run_name,
            "dataset_name": r.dataset_name,
            "total_queries": r.total_queries,
            "passed_queries": r.passed_queries,
            "metrics": r.metrics_summary,
            "created_at": r.created_at,
        })
    return jsonify({
        "success": True,
        "data": results,
    }), 200

