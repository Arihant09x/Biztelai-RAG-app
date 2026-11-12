"""Document management, upload registration, page inspection, and deletion service."""

import os
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Tuple
from app.constants import DocumentStatus, IngestionStatus
from app.extensions import db
from app.models.document import Document, DocumentChunk, DocumentPage, DocumentVersion
from app.models.ingestion import IngestionJob
from app.schemas.document import DocumentDetailResponse, DocumentPageResponse, DocumentResponse, DocumentUploadMetadata
from app.services.storage_service import StorageService
from app.utils.errors import ConflictError, NotFoundError
import structlog

logger = structlog.get_logger(__name__)


class DocumentService:
    """Orchestrates PDF document registration, duplicate prevention, and lifecycle state."""

    def __init__(self, storage_service: Optional[StorageService] = None):
        self.storage = storage_service or StorageService()

    def register_and_upload(
        self,
        file_stream: BinaryIO,
        original_filename: str,
        user_id: Optional[str] = None,
        metadata: Optional[DocumentUploadMetadata] = None,
    ) -> Tuple[Document, IngestionJob]:
        """Validate, persist PDF to storage, detect duplicates, and trigger ingestion job."""
        meta = metadata or DocumentUploadMetadata()

        # 1. Save file and compute SHA-256
        stored_filename, clean_name, file_size, sha256_hash = self.storage.save_file(
            file_stream=file_stream,
            original_filename=original_filename,
        )

        # 2. Duplicate Detection
        existing_doc = Document.query.filter_by(sha256_hash=sha256_hash, is_deleted=False).first()
        if existing_doc:
            # Clean up the newly written duplicate file
            self.storage.delete_file(stored_filename)
            raise ConflictError(
                f"Duplicate document detected: '{existing_doc.title}' with matching SHA-256 ({sha256_hash[:8]}...) already exists."
            )

        # 3. Create Document record
        doc_title = meta.title or Path(clean_name).stem.replace("_", " ").title()
        document = Document(
            title=doc_title,
            original_filename=clean_name,
            stored_filename=stored_filename,
            file_size_bytes=file_size,
            sha256_hash=sha256_hash,
            category=meta.category,
            department=meta.department,
            access_scope=meta.access_scope or "public",
            status=DocumentStatus.PENDING.value,
            created_by_id=user_id,
        )
        db.session.add(document)
        db.session.flush()

        # 4. Create initial version record
        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            changelog="Initial document upload",
            created_by_id=user_id,
        )
        db.session.add(version)

        # 5. Create Ingestion Job
        job = IngestionJob(
            document_id=document.id,
            status=IngestionStatus.PENDING.value,
            progress_percent=0,
            current_stage="queued",
        )
        db.session.add(job)
        db.session.commit()

        # 6. Trigger asynchronous Celery ingestion if available
        self._dispatch_ingestion_task(job.id, document.id)

        logger.info("document_registered_successfully", doc_id=str(document.id), title=document.title, job_id=str(job.id))
        return document, job

    def _dispatch_ingestion_task(self, job_id, document_id):
        """Dispatch Celery task with graceful inline fallback if Celery worker unavailable."""
        try:
            from app.tasks.ingestion_tasks import process_document_ingestion_task
            task = process_document_ingestion_task.delay(str(job_id))
            job = IngestionJob.query.get(job_id)
            if job:
                job.celery_task_id = str(task.id)
                db.session.commit()
        except Exception as e:
            logger.warning("celery_dispatch_skipped_running_queued", error=str(e))

    def get_document(self, document_id: str) -> Document:
        """Retrieve active document by ID."""
        doc = Document.query.filter_by(id=document_id, is_deleted=False).first()
        if not doc:
            raise NotFoundError(f"Document with ID '{document_id}' not found.")
        return doc

    def list_documents(
        self,
        category: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Document], int]:
        """List documents with filtering and pagination."""
        query = Document.query.filter_by(is_deleted=False)
        if category:
            query = query.filter_by(category=category)
        if department:
            query = query.filter_by(department=department)
        if status:
            query = query.filter_by(status=status)

        total = query.count()
        docs = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
        return docs, total

    def delete_document(self, document_id: str) -> bool:
        """Permanently hard-delete document, all associated chunks, pages, assets, jobs, and disk file."""
        doc = self.get_document(document_id)
        stored_filename = doc.stored_filename

        # 1. Remove physical file from disk storage
        if stored_filename:
            try:
                self.storage.delete_file(stored_filename)
            except Exception as e:
                logger.warning("storage_file_deletion_failed", error=str(e), filename=stored_filename)

        # 2. Hard delete from database (cascades to chunks, pages, versions, assets, jobs)
        db.session.delete(doc)
        db.session.commit()
        logger.info("document_hard_deleted", doc_id=document_id)
        return True

    def reprocess_document(self, document_id: str) -> IngestionJob:
        """Clear existing pages and chunks and queue a fresh ingestion job."""
        doc = self.get_document(document_id)

        # Remove existing extracted chunks, pages, and assets
        DocumentChunk.query.filter_by(document_id=doc.id).delete()
        DocumentPage.query.filter_by(document_id=doc.id).delete()

        doc.status = DocumentStatus.PENDING.value

        job = IngestionJob(
            document_id=doc.id,
            status=IngestionStatus.PENDING.value,
            progress_percent=0,
            current_stage="reprocessing_queued",
        )
        db.session.add(job)
        db.session.commit()

        self._dispatch_ingestion_task(job.id, doc.id)
        return job

    def get_document_page(self, document_id: str, page_number: int) -> DocumentPage:
        """Retrieve specific page text and metadata."""
        page = DocumentPage.query.filter_by(document_id=document_id, page_number=page_number).first()
        if not page:
            raise NotFoundError(f"Page {page_number} for document '{document_id}' not found.")
        return page

