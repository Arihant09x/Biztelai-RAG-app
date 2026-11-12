#!/usr/bin/env python3
"""Database Schema Migration and Sample SOP Seeding for PostgreSQL / pgvector."""

import os
import sys
from pathlib import Path

# Add project root
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.constants import UserRole, DocumentStatus
from app.models import (
    Role, User, Document, DocumentPage, DocumentChunk,
    EmbeddingModel, IndexVersion
)
from app.utils.security import compute_sha256, hash_password
from app.services.storage_service import StorageService
from app.services.pdf_extraction_service import PDFExtractionService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from scripts.seed_sample_data import SOP_DEFINITIONS, create_pdf


def run_migration_and_seed():
    print("=" * 70)
    print("BIZTELAI MANUFACTURING SOP COPILOT - DB MIGRATION & SEEDING")
    print("=" * 70)

    db_url = os.getenv("DATABASE_URL")
    print(f"Target Database: {db_url.split('@')[-1] if '@' in db_url else 'local'}")

    app = create_app()

    with app.app_context():
        # 1. Ensure pgvector extension exists if PostgreSQL
        engine = db.engine
        dialect_name = engine.dialect.name
        print(f"Database Dialect: {dialect_name}")

        if dialect_name == "postgresql":
            print("Ensuring pgvector extension is enabled...")
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
            print("[PASS] pgvector extension enabled.")

        # 2. Create all tables
        print("Creating all database tables via SQLAlchemy metadata...")
        import app.models  # Register all models
        db.create_all()
        print("[PASS] All tables created successfully.")

        # 3. Create full-text and vector indexes on PostgreSQL
        if dialect_name == "postgresql":
            print("Verifying / Creating specialized vector and FTS indexes...")
            with engine.connect() as conn:
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_cosine 
                        ON document_chunks USING ivfflat (embedding vector_cosine_ops) 
                        WITH (lists = 10);
                    """))
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_document_chunks_fts 
                        ON document_chunks USING gin (to_tsvector('english', content));
                    """))
                    conn.commit()
                    print("[PASS] Vector ivfflat and FTS GIN indexes created.")
                except Exception as ie:
                    print(f"[INFO] Note on indexes (e.g. table empty or index exists): {ie}")

        # 4. Seed Roles
        print("\nSeeding user roles...")
        roles_data = [
            (UserRole.ADMIN.value, "System Administrator with full access"),
            (UserRole.SUPERVISOR.value, "Manufacturing Supervisor with upload & procedure rights"),
            (UserRole.OPERATOR.value, "Plant Operator with read and query rights"),
            (UserRole.AUDITOR.value, "Compliance Auditor with read-only audit access"),
        ]
        role_map = {}
        for r_name, r_desc in roles_data:
            role = Role.query.filter_by(name=r_name).first()
            if not role:
                role = Role(name=r_name, description=r_desc)
                db.session.add(role)
                db.session.flush()
            role_map[r_name] = role

        # 5. Seed Users
        print("Seeding default test accounts...")
        users_to_seed = [
            ("supervisor@biztelai.com", "Password123!", "Rajesh Kumar (Supervisor)", "Machining", UserRole.SUPERVISOR.value),
            ("admin@biztelai.com", "AdminSecret123!", "System Administrator", "IT", UserRole.ADMIN.value),
            ("operator@biztelai.com", "Operator123!", "Amit Sharma (Operator)", "Forming", UserRole.OPERATOR.value),
        ]

        supervisor_user = None
        for email, password, full_name, dept, role_name in users_to_seed:
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    password_hash=hash_password(password),
                    full_name=full_name,
                    department=dept,
                    role_id=role_map[role_name].id,
                    is_active=True,
                )
                db.session.add(user)
                db.session.flush()
                print(f"  + Created user: {email} ({role_name})")
            else:
                print(f"  * User exists: {email}")

            if role_name == UserRole.SUPERVISOR.value:
                supervisor_user = user

        db.session.commit()

        # 6. Seed Embedding Model Record
        emb_model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        emb_dim = int(os.getenv("EMBEDDING_DIMENSION", "384"))
        emb_rec = EmbeddingModel.query.filter_by(name=emb_model_name).first()
        if not emb_rec:
            emb_rec = EmbeddingModel(
                name=emb_model_name,
                dimension=emb_dim,
                provider="sentence_transformers",
                is_active=True,
            )
            db.session.add(emb_rec)
            db.session.commit()
            print(f"Registered active embedding model: {emb_model_name} (dim {emb_dim})")

        # 7. Generate and Ingest Sample Manufacturing SOPs
        print("\nIngesting Sample Manufacturing SOPs...")
        sops_dir = ROOT_DIR / "sample_data" / "sops"
        sops_dir.mkdir(parents=True, exist_ok=True)

        storage = StorageService()
        pdf_extractor = PDFExtractionService()
        chunker = ChunkingService(target_chunk_tokens=700, overlap_tokens=100)
        embedding_service = EmbeddingService()

        for sop in SOP_DEFINITIONS:
            pdf_path = sops_dir / sop["filename"]
            create_pdf(pdf_path, sop["pages"], sop["title"])

            with open(pdf_path, "rb") as f:
                sha256 = compute_sha256(pdf_path)
                existing_doc = Document.query.filter_by(sha256_hash=sha256, is_deleted=False).first()
                if existing_doc:
                    print(f"  * Document '{sop['title']}' already indexed (ID: {existing_doc.id}). Skipping.")
                    continue

                stored_fn, clean_name, file_size, _ = storage.save_file(f, sop["filename"])

                doc = Document(
                    title=sop["title"],
                    original_filename=clean_name,
                    stored_filename=stored_fn,
                    file_size_bytes=file_size,
                    sha256_hash=sha256,
                    category=sop["category"],
                    department=sop["department"],
                    status=DocumentStatus.INDEXED.value,
                    created_by_id=supervisor_user.id,
                )
                db.session.add(doc)
                db.session.flush()

                # Extract pages
                extraction_res = pdf_extractor.extract(pdf_path)
                page_id_map = {}
                for p in extraction_res.pages:
                    dp = DocumentPage(
                        document_id=doc.id,
                        page_number=p.page_number,
                        raw_text=p.text,
                        has_ocr=False,
                    )
                    db.session.add(dp)
                    db.session.flush()
                    page_id_map[p.page_number] = dp.id

                # Chunk document
                chunks = chunker.chunk_document(
                    extraction_res.pages,
                    document_id=str(doc.id),
                    document_title=doc.title,
                    category=doc.category,
                    department=doc.department,
                )

                # Batch embed chunks
                chunk_texts = [c.content for c in chunks]
                embeddings = embedding_service.provider.embed_texts(chunk_texts)

                for c_obj, emb in zip(chunks, embeddings):
                    dc = DocumentChunk(
                        document_id=doc.id,
                        page_id=page_id_map.get(c_obj.page_number),
                        chunk_index=c_obj.chunk_index,
                        section_heading=c_obj.section_heading,
                        subheading=c_obj.subheading,
                        content=c_obj.content,
                        token_count=c_obj.token_count,
                        embedding=emb,
                        is_active=True,
                        metadata_json={"model": emb_model_name, **c_obj.metadata},
                    )
                    db.session.add(dc)

                db.session.commit()
                print(f"  + Indexed '{sop['title']}' -> {len(chunks)} chunks with 384-dim vectors.")

        print("\n" + "=" * 70)
        print("DATABASE MIGRATION & SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 70)


if __name__ == "__main__":
    run_migration_and_seed()
