#!/usr/bin/env python3
"""Clean demo data and ingest the 4 authentic BiztelAI assessment SOP PDFs into PostgreSQL/pgvector.

Preserves:
- Users (admin, supervisor, operator)
- Database schema and pgvector extensions
- Audit logs schema
"""

import os
import sys
import shutil
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env", override=True)

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.document import Document, DocumentVersion, DocumentPage, DocumentChunk, DocumentAsset
from app.models.ingestion import IngestionJob
from app.models.conversation import Conversation, Message, MessageSource
from app.models.feedback import Feedback
from app.models.audit import AuditLog
from app.services.pdf_extraction_service import PDFExtractionService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.storage_service import StorageService
from app.constants import DocumentStatus, IngestionStatus

SOPS = [
    {
        "filename": "SOP-101-CNC-Spindle-Maintenance.pdf",
        "title": "CNC Spindle Maintenance and Bearing Lubrication",
        "category": "maintenance",
        "department": "CNC Machining Center",
        "access_scope": "public",
    },
    {
        "filename": "SOP-204-Emergency-Lockout-Tagout.pdf",
        "title": "Hazardous Energy Control (Lockout / Tagout) Procedure",
        "category": "safety",
        "department": "Plant-Wide Electrical / Mechanical",
        "access_scope": "public",
    },
    {
        "filename": "SOP-305-Hydraulic-Press-Safety.pdf",
        "title": "Hydraulic Stamping Press Safety and Operating Procedure",
        "category": "sop",
        "department": "Stamping Press Unit HP-200",
        "access_scope": "public",
    },
    {
        "filename": "SOP-402-Quality-Inspection-Calipers.pdf",
        "title": "Digital Vernier Caliper Calibration and Quality Verification",
        "category": "quality",
        "department": "Quality Assurance Lab",
        "access_scope": "public",
    },
]


def clean_demo_data():
    """Show affected records and safely purge demo data while keeping real users."""
    print("\n" + "=" * 70)
    print("  PHASE 8: SAFELY CLEAN DEMO DATABASE DATA")
    print("=" * 70)

    # Count existing records
    doc_count = Document.query.count()
    ver_count = DocumentVersion.query.count()
    page_count = DocumentPage.query.count()
    chunk_count = DocumentChunk.query.count()
    asset_count = DocumentAsset.query.count()
    job_count = IngestionJob.query.count()
    conv_count = Conversation.query.count()
    msg_count = Message.query.count()
    src_count = MessageSource.query.count()
    fb_count = Feedback.query.count()
    user_count = User.query.count()

    print(f"Current Database Counts:")
    print(f"  - Users (Preserved):      {user_count}")
    print(f"  - Documents:              {doc_count}")
    print(f"  - Document Versions:      {ver_count}")
    print(f"  - Document Pages:         {page_count}")
    print(f"  - Document Chunks:        {chunk_count}")
    print(f"  - Document Assets:        {asset_count}")
    print(f"  - Ingestion Jobs:         {job_count}")
    print(f"  - Conversations:          {conv_count}")
    print(f"  - Messages:               {msg_count}")
    print(f"  - Message Sources:        {src_count}")
    print(f"  - Feedback Records:       {fb_count}")

    # Transactional cleanup
    print("\nExecuting transactional deletion of demo data...")
    try:
        Feedback.query.delete()
        MessageSource.query.delete()
        Message.query.delete()
        Conversation.query.delete()
        DocumentChunk.query.delete()
        DocumentAsset.query.delete()
        DocumentPage.query.delete()
        DocumentVersion.query.delete()
        IngestionJob.query.delete()
        Document.query.delete()
        db.session.commit()
        print("✓ All demo documents, chunks, pages, jobs, and conversations removed successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"✗ Cleanup failed: {e}")
        raise e


def ingest_assessment_documents():
    """Ingest the 4 assessment SOPs into PostgreSQL and pgvector."""
    print("\n" + "=" * 70)
    print("  PHASE 9: INGEST THE FOUR AUTHENTIC ASSESSMENT DOCUMENTS")
    print("=" * 70)

    storage_service = StorageService()
    storage_dir = storage_service.base_dir
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Also ensure root data/documents exists for local compatibility
    root_data_dir = BACKEND_DIR.parent / "data" / "documents"
    root_data_dir.mkdir(parents=True, exist_ok=True)

    sops_source_dir = BACKEND_DIR / "sample_data" / "sops"
    if not sops_source_dir.exists():
        raise FileNotFoundError(f"SOP source directory not found: {sops_source_dir}")

    # Find supervisor user to assign document creator
    supervisor = User.query.filter(User.role.has(name="supervisor")).first() or User.query.first()
    creator_id = supervisor.id if supervisor else None

    pdf_extractor = PDFExtractionService(ocr_enabled=True)
    chunker = ChunkingService(target_chunk_tokens=700, overlap_tokens=100)
    embedding_service = EmbeddingService()

    for sop_meta in SOPS:
        filename = sop_meta["filename"]
        source_path = sops_source_dir / filename

        if not source_path.exists():
            print(f"✗ File missing: {source_path}")
            continue

        print(f"\nProcessing: {filename} ({sop_meta['title']})...")

        with open(source_path, "rb") as f:
            pdf_bytes = f.read()

        file_size = len(pdf_bytes)
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        stored_filename = f"{uuid.uuid4().hex}_{filename}"

        # Copy to primary storage directory
        dest_primary = storage_dir / stored_filename
        with open(dest_primary, "wb") as f:
            f.write(pdf_bytes)

        # Copy to root fallback storage directory
        dest_root = root_data_dir / stored_filename
        with open(dest_root, "wb") as f:
            f.write(pdf_bytes)

        # 1. Create Document
        doc = Document(
            title=sop_meta["title"],
            original_filename=filename,
            stored_filename=stored_filename,
            file_size_bytes=file_size,
            sha256_hash=sha256,
            category=sop_meta["category"],
            department=sop_meta["department"],
            access_scope=sop_meta["access_scope"],
            status=DocumentStatus.INDEXED.value,
            created_by_id=creator_id,
            metadata_json={"source": "BiztelAI Official Assessment"},
        )
        db.session.add(doc)
        db.session.flush()

        # 2. Create Document Version
        version = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            changelog="Authentic assessment SOP baseline ingestion",
            created_by_id=creator_id,
        )
        db.session.add(version)

        # 3. Create Ingestion Job Record
        job = IngestionJob(
            document_id=doc.id,
            status=IngestionStatus.COMPLETED.value,
            progress_percent=100,
            current_stage="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        db.session.add(job)
        db.session.flush()

        # 4. Extract Pages with PyMuPDF
        extraction = pdf_extractor.extract(dest_primary)
        print(f"  - Extracted {len(extraction.pages)} pages")

        page_map = {}
        for p in extraction.pages:
            doc_page = DocumentPage(
                document_id=doc.id,
                page_number=p.page_number,
                raw_text=p.text,
                has_ocr=p.has_ocr,
                page_metadata=p.metadata,
            )
            db.session.add(doc_page)
            db.session.flush()
            page_map[p.page_number] = doc_page.id

            # Save tables as assets if any
            for tbl in p.tables:
                asset = DocumentAsset(
                    document_id=doc.id,
                    page_number=p.page_number,
                    asset_type="table",
                    caption_or_title=tbl.title or f"Table on page {p.page_number}",
                    content_json={"headers": tbl.headers, "rows": tbl.rows},
                )
                db.session.add(asset)

        # 5. Structure-Aware Chunking
        chunks = chunker.chunk_document(
            pages=extraction.pages,
            document_id=str(doc.id),
            document_title=doc.title,
            category=doc.category,
            department=doc.department,
        )
        print(f"  - Created {len(chunks)} structure-aware chunks")

        # 6. Generate 384-dimensional Embeddings
        chunk_texts = [c.content for c in chunks]
        embeddings = embedding_service.provider.embed_texts(chunk_texts)

        for c_obj, emb in zip(chunks, embeddings):
            doc_chunk = DocumentChunk(
                document_id=doc.id,
                page_id=page_map.get(c_obj.page_number),
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

        db.session.commit()
        print(f"  ✓ Indexed '{doc.title}' ({len(extraction.pages)} pages, {len(chunks)} chunks, {len(embeddings)} vectors)")

    print("\n" + "=" * 70)
    print("  FINAL DATABASE VERIFICATION")
    print("=" * 70)
    docs = Document.query.all()
    print(f"Total Active Documents: {len(docs)}")
    for d in docs:
        p_count = DocumentPage.query.filter_by(document_id=d.id).count()
        c_count = DocumentChunk.query.filter_by(document_id=d.id).count()
        print(f"  - [{d.category.upper()}] {d.title} (ID: {d.id}, Pages: {p_count}, Chunks: {c_count})")
    print(f"Total pgvector Chunks in DB: {DocumentChunk.query.count()}")
    print("✓ Assessment ingestion completed successfully.")


def prime_dns_cache():
    """Ensure host is in DNS cache on Windows to avoid getaddrinfo timeout."""
    import socket
    import time
    host = "ep-noisy-bonus-b3o3sjfv-pooler.c-4.ap-southeast-1.aws.neon.tech"
    for _ in range(5):
        try:
            socket.getaddrinfo(host, 5432, socket.AF_INET)
            break
        except Exception:
            time.sleep(1)


if __name__ == "__main__":
    prime_dns_cache()
    app = create_app("development")
    with app.app_context():
        clean_demo_data()
        ingest_assessment_documents()
