"""Document management, upload, inspection, and page retrieval endpoints."""

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required
from pydantic import ValidationError as PydanticValidationError
from app.api.deps import admin_required, get_current_user, supervisor_required
from app.constants import AuditAction
from app.models.document import DocumentChunk, DocumentPage
from app.models.ingestion import IngestionJob
from app.schemas.document import DocumentDetailResponse, DocumentPageResponse, DocumentResponse, DocumentUploadMetadata
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.utils.errors import FileUploadError, ValidationError

documents_bp = Blueprint("documents", __name__)
doc_service = DocumentService()


@documents_bp.route("/documents/upload", methods=["POST"])
@jwt_required()
@supervisor_required
def upload_document():
    """Upload PDF SOP file with metadata and initiate background ingestion."""
    user = get_current_user()

    if "file" not in request.files:
        raise FileUploadError("No file uploaded. Request must include multipart 'file' field.")

    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        raise FileUploadError("Uploaded file cannot have an empty filename.")

    # Read form metadata
    metadata = DocumentUploadMetadata(
        title=request.form.get("title"),
        category=request.form.get("category", "General"),
        department=request.form.get("department"),
        access_scope=request.form.get("access_scope", "public"),
    )

    doc, job = doc_service.register_and_upload(
        file_stream=uploaded_file.stream,
        original_filename=uploaded_file.filename,
        user_id=str(user.id),
        metadata=metadata,
    )

    AuditService.log_event(
        action=AuditAction.DOC_UPLOAD.value,
        user_id=str(user.id),
        target_type="document",
        target_id=str(doc.id),
        details={"filename": doc.original_filename, "size_bytes": doc.file_size_bytes},
    )

    return jsonify({
        "success": True,
        "message": "Document registered and queued for ingestion.",
        "data": {
            "document": DocumentResponse.model_validate(doc).model_dump(),
            "job_id": str(job.id),
            "status": job.status,
        },
    }), 202


@documents_bp.route("/documents", methods=["GET"])
@jwt_required()
def list_documents():
    """List documents with optional filtering and pagination."""
    category = request.args.get("category")
    department = request.args.get("department")
    status = request.args.get("status")
    skip = int(request.args.get("skip", 0))
    limit = min(int(request.args.get("limit", 50)), 100)

    docs, total = doc_service.list_documents(
        category=category,
        department=department,
        status=status,
        skip=skip,
        limit=limit,
    )

    items = [DocumentResponse.model_validate(d).model_dump() for d in docs]
    return jsonify({
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        },
    }), 200


@documents_bp.route("/documents/<document_id>", methods=["GET"])
@jwt_required()
def get_document(document_id: str):
    """Retrieve detailed document metadata including pages and chunk counts."""
    doc = doc_service.get_document(document_id)
    page_count = DocumentPage.query.filter_by(document_id=doc.id).count()
    chunk_count = DocumentChunk.query.filter_by(document_id=doc.id).count()

    doc_data = DocumentResponse.model_validate(doc).model_dump()
    doc_data["total_pages"] = page_count
    doc_data["total_chunks"] = chunk_count

    return jsonify({
        "success": True,
        "data": doc_data,
    }), 200


@documents_bp.route("/documents/<document_id>", methods=["DELETE"])
@jwt_required()
@supervisor_required
def delete_document(document_id: str):
    """Soft delete document and remove underlying storage file."""
    user = get_current_user()
    doc_service.delete_document(document_id)

    AuditService.log_event(
        action=AuditAction.DOC_DELETE.value,
        user_id=str(user.id),
        target_type="document",
        target_id=document_id,
    )

    return jsonify({
        "success": True,
        "message": f"Document '{document_id}' successfully deleted.",
    }), 200


@documents_bp.route("/documents/<document_id>/reprocess", methods=["POST"])
@jwt_required()
@supervisor_required
def reprocess_document(document_id: str):
    """Trigger re-extraction, re-chunking, and re-indexing of a document."""
    user = get_current_user()
    job = doc_service.reprocess_document(document_id)

    AuditService.log_event(
        action=AuditAction.DOC_REPROCESS.value,
        user_id=str(user.id),
        target_type="document",
        target_id=document_id,
        details={"job_id": str(job.id)},
    )

    return jsonify({
        "success": True,
        "message": "Document re-processing queued.",
        "data": {"job_id": str(job.id), "status": job.status},
    }), 202


@documents_bp.route("/documents/<document_id>/status", methods=["GET"])
@jwt_required()
def get_document_status(document_id: str):
    """Retrieve current ingestion status and progress for a document."""
    doc = doc_service.get_document(document_id)
    latest_job = (
        IngestionJob.query.filter_by(document_id=doc.id)
        .order_by(IngestionJob.created_at.desc())
        .first()
    )

    return jsonify({
        "success": True,
        "data": {
            "document_id": str(doc.id),
            "document_status": doc.status,
            "latest_job": {
                "id": str(latest_job.id) if latest_job else None,
                "status": latest_job.status if latest_job else None,
                "progress_percent": latest_job.progress_percent if latest_job else 0,
                "current_stage": latest_job.current_stage if latest_job else None,
                "error_message": latest_job.error_message if latest_job else None,
            } if latest_job else None,
        },
    }), 200


@documents_bp.route("/documents/<document_id>/pages/<int:page_number>", methods=["GET"])
@jwt_required()
def get_page(document_id: str, page_number: int):
    """Retrieve exact extracted text and metadata for a specific document page."""
    page = doc_service.get_document_page(document_id, page_number)
    return jsonify({
        "success": True,
        "data": DocumentPageResponse.model_validate(page).model_dump(),
    }), 200


@documents_bp.route("/documents/<document_id>/file", methods=["GET"])
@jwt_required(optional=True)
def get_document_file(document_id: str):
    """Retrieve raw PDF file for in-browser PDF.js rendering with HTTP Range support."""
    from app.utils.errors import NotFoundError, AuthenticationError
    from flask_jwt_extended import get_jwt_identity, decode_token

    # Verify authentication either via header (JWT identity) or query param
    identity = get_jwt_identity()
    if not identity:
        query_token = request.args.get("token")
        if query_token:
            if query_token.startswith("Bearer "):
                query_token = query_token[7:]
            try:
                decoded = decode_token(query_token)
                identity = decoded.get("sub")
            except Exception:
                raise AuthenticationError("Invalid or expired document access token.")
        if not identity:
            raise AuthenticationError("Authentication token required to view document file.")

    doc = doc_service.get_document(document_id)
    file_path = doc_service.storage.get_file_path(doc.stored_filename)
    if not file_path.exists():
        raise NotFoundError(f"PDF file for document '{document_id}' not found on storage disk.")

    safe_filename = (doc.original_filename or "document.pdf").replace('"', '').replace('\n', '').replace('\r', '')
    response = send_file(
        str(file_path),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=safe_filename,
        conditional=True,
    )
    response.headers["Accept-Ranges"] = "bytes"
    response.headers["Content-Disposition"] = f'inline; filename="{safe_filename}"'
    return response


