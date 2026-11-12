"""Ingestion job monitoring endpoints."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.models.ingestion import IngestionJob
from app.schemas.ingestion import IngestionJobResponse
from app.utils.errors import NotFoundError

ingestion_bp = Blueprint("ingestion", __name__)


@ingestion_bp.route("/ingestion/jobs", methods=["GET"])
@jwt_required()
def list_jobs():
    """List recent ingestion jobs with optional status filter."""
    doc_id = request.args.get("document_id")
    status = request.args.get("status")
    limit = min(int(request.args.get("limit", 20)), 100)

    query = IngestionJob.query
    if doc_id:
        query = query.filter_by(document_id=doc_id)
    if status:
        query = query.filter_by(status=status)

    jobs = query.order_by(IngestionJob.created_at.desc()).limit(limit).all()
    items = [IngestionJobResponse.model_validate(j).model_dump() for j in jobs]

    return jsonify({
        "success": True,
        "data": items,
    }), 200


@ingestion_bp.route("/ingestion/jobs/<job_id>", methods=["GET"])
@jwt_required()
def get_job(job_id: str):
    """Retrieve detailed progress and status of a specific background ingestion job."""
    job = IngestionJob.query.get(job_id)
    if not job:
        # Fallback: check if the client provided document_id instead of job_id
        job = IngestionJob.query.filter_by(document_id=job_id).order_by(IngestionJob.created_at.desc()).first()
    if not job:
        raise NotFoundError(f"Ingestion job '{job_id}' not found.")

    return jsonify({
        "success": True,
        "data": IngestionJobResponse.model_validate(job).model_dump(),
    }), 200

