"""Celery asynchronous tasks for PDF document extraction, chunking, and embedding."""

import logging
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from app.constants import DocumentStatus, IngestionStatus
from app.extensions import db
from app.models.document import Document, DocumentAsset, DocumentChunk, DocumentPage
from app.models.ingestion import IngestionJob
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.pdf_extraction_service import PDFExtractionService
from app.services.storage_service import StorageService
from app.tasks.celery_app import celery
import structlog

logger = structlog.get_logger(__name__)
celery_logger = logging.getLogger("celery.task")


def _log_stage(stage_num: int, total_stages: int, title: str, details: str = ""):
    """Print high-visibility status to Celery worker console."""
    msg = f"[CELERY WORKER] [{stage_num}/{total_stages}] {title.upper()}"
    if details:
        msg += f" -> {details}"
    celery_logger.info(msg)
    print(f"\n>>> {msg}", flush=True)


@celery.task(bind=True, max_retries=3, default_retry_delay=10)
def process_document_ingestion_task(self, job_id: str):
    """Asynchronous background worker task executing full PDF ingestion pipeline."""
    from app import create_app
    app = create_app()

    with app.app_context():
        job = IngestionJob.query.get(job_id)
        if not job:
            logger.error("ingestion_job_not_found", job_id=job_id)
            print(f"\n[CELERY WORKER ERROR] Ingestion job '{job_id}' not found in database.", flush=True)
            return {"status": "failed", "reason": "job_not_found"}

        document = Document.query.get(job.document_id)
        if not document:
            job.status = IngestionStatus.FAILED.value
            job.error_message = "Associated document record missing"
            db.session.commit()
            print(f"\n[CELERY WORKER ERROR] Document record missing for Job '{job_id}'.", flush=True)
            return {"status": "failed", "reason": "document_missing"}

        _log_stage(1, 6, "INITIALIZING INGESTION PIPELINE", f"Document: '{document.title}' (ID: {document.id})")

        # Mark job and document as processing
        job.status = IngestionStatus.PROCESSING.value
        job.started_at = datetime.now(timezone.utc)
        job.current_stage = "validating_file"
        job.progress_percent = 10
        document.status = DocumentStatus.PROCESSING.value
        db.session.commit()

        storage_service = StorageService()
        pdf_extractor = PDFExtractionService(ocr_enabled=app.config.get("OCR_ENABLED", True))
        chunker = ChunkingService(
            target_chunk_tokens=app.config.get("CHUNK_SIZE", 700),
            overlap_tokens=app.config.get("CHUNK_OVERLAP", 100),
        )
        embedding_service = EmbeddingService()

        try:
            # 1. Resolve stored PDF file
            file_path = storage_service.get_file_path(document.stored_filename)
            _log_stage(2, 6, "EXTRACTING PDF TEXT, TABLES & LAYOUT", f"Source: {Path(file_path).name}")

            t0 = time.time()
            job.current_stage = "extracting_pages"
            job.progress_percent = 25
            db.session.commit()

            extraction_result = pdf_extractor.extract(file_path)
            extract_duration = time.time() - t0

            # Check if OCR was applied on any page
            if any(p.has_ocr for p in extraction_result.pages):
                job.current_stage = "ocr_processing"
                job.progress_percent = 40
                db.session.commit()
                _log_stage(2, 6, "OCR POST-PROCESSING APPLIED", f"{sum(1 for p in extraction_result.pages if p.has_ocr)} pages scanned")

            total_tables = sum(len(p.tables) for p in extraction_result.pages)
            _log_stage(
                2,
                6,
                "PDF EXTRACTION COMPLETE",
                f"{len(extraction_result.pages)} pages, {total_tables} tables in {extract_duration:.2f}s",
            )

            # Update document title from metadata if available and not explicitly set
            if extraction_result.document_title and not document.metadata_json.get("title_overridden"):
                document.metadata_json = {**document.metadata_json, **extraction_result.metadata}

            # 3. Store Pages
            _log_stage(3, 6, "PERSISTING DOCUMENT PAGES TO DATABASE", f"{len(extraction_result.pages)} pages")
            job.current_stage = "saving_pages"
            job.progress_percent = 50
            db.session.commit()

            page_id_map: Dict[int, Any] = {}
            for page in extraction_result.pages:
                doc_page = DocumentPage(
                    document_id=document.id,
                    page_number=page.page_number,
                    raw_text=page.text,
                    has_ocr=page.has_ocr,
                    page_metadata=page.metadata,
                )
                db.session.add(doc_page)
                db.session.flush()
                page_id_map[page.page_number] = doc_page.id

                # Save extracted tables as assets
                for tbl in page.tables:
                    asset = DocumentAsset(
                        document_id=document.id,
                        page_number=page.page_number,
                        asset_type="table",
                        caption_or_title=tbl.title or f"Table on page {page.page_number}",
                        content_json={"headers": tbl.headers, "rows": tbl.rows},
                    )
                    db.session.add(asset)

            # 4. Chunking
            _log_stage(4, 6, "STRUCTURE-AWARE CHUNKING", f"Target tokens: {chunker.target_chunk_tokens}")
            job.current_stage = "chunking"
            job.progress_percent = 65
            db.session.commit()

            processed_chunks = chunker.chunk_document(
                pages=extraction_result.pages,
                document_id=str(document.id),
                document_title=document.title,
                category=document.category,
                department=document.department,
            )
            _log_stage(4, 6, "CHUNKING COMPLETE", f"Created {len(processed_chunks)} semantic chunks")

            # 5. Embeddings Generation
            _log_stage(5, 6, "GENERATING VECTOR EMBEDDINGS (MiniLM-L6-v2)", f"Encoding {len(processed_chunks)} chunks...")
            job.current_stage = "generating_embeddings"
            job.progress_percent = 80
            db.session.commit()

            t_emb = time.time()
            chunk_texts = [c.content for c in processed_chunks]
            embeddings = embedding_service.provider.embed_texts(chunk_texts)
            emb_duration = time.time() - t_emb
            dim = len(embeddings[0]) if embeddings else 0
            _log_stage(5, 6, "EMBEDDINGS GENERATED", f"{len(embeddings)} vectors (dim {dim}) in {emb_duration:.2f}s")

            # 6. Store Chunks with Embeddings & Vector Indexing
            _log_stage(6, 6, "STORING CHUNKS & PGVECTOR INDEXING", f"Writing {len(processed_chunks)} chunks to PostgreSQL...")
            job.current_stage = "vector_indexing"
            job.progress_percent = 90
            db.session.commit()

            t_vec = time.time()
            for c_obj, emb in zip(processed_chunks, embeddings):
                doc_chunk = DocumentChunk(
                    document_id=document.id,
                    page_id=page_id_map.get(c_obj.page_number),
                    chunk_index=c_obj.chunk_index,
                    section_heading=c_obj.section_heading,
                    subheading=c_obj.subheading,
                    content=c_obj.content,
                    token_count=c_obj.token_count,
                    is_active=True,
                    metadata_json=c_obj.metadata,
                    embedding=emb,
                )
                db.session.add(doc_chunk)

            # 7. Finalize Complete Ingestion
            job.status = IngestionStatus.COMPLETED.value
            job.progress_percent = 100
            job.current_stage = "completed"
            job.completed_at = datetime.now(timezone.utc)
            document.status = DocumentStatus.INDEXED.value

            db.session.commit()
            vec_duration = time.time() - t_vec

            print("\n" + "=" * 70, flush=True)
            print(f" [CELERY WORKER] INGESTION PIPELINE SUCCEEDED!", flush=True)
            print(f"  * Document:     {document.title} (ID: {document.id})", flush=True)
            print(f"  * Pages:        {len(extraction_result.pages)}", flush=True)
            print(f"  * Chunks:       {len(processed_chunks)} (Stored in pgvector in {vec_duration:.2f}s)", flush=True)
            print(f"  * Status:       INDEXED / READY FOR SEARCH", flush=True)
            print("=" * 70 + "\n", flush=True)

            logger.info(
                "ingestion_job_completed",
                job_id=job_id,
                doc_id=str(document.id),
                total_pages=len(extraction_result.pages),
                total_chunks=len(processed_chunks),
            )
            return {"status": "completed", "chunks": len(processed_chunks), "pages": len(extraction_result.pages)}

        except Exception as exc:
            db.session.rollback()
            err_str = str(exc)
            logger.error("ingestion_job_exception", job_id=job_id, error=err_str, exc_info=True)

            print("\n" + "!" * 70, flush=True)
            print(f" [CELERY WORKER ERROR] Ingestion failed for Job {job_id}", flush=True)
            print(f" Error: {err_str}", flush=True)
            print("!" * 70 + "\n", flush=True)
            traceback.print_exc()

            # Clean up chunks so no incomplete embedding sets remain
            try:
                DocumentChunk.query.filter_by(document_id=document.id).delete()
            except Exception:
                pass

            job.status = IngestionStatus.FAILED.value
            job.error_message = err_str
            job.retry_count += 1
            document.status = DocumentStatus.FAILED.value
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

            return {"status": "failed", "error": err_str}

