"""Document, Version, Page, Chunk, and Asset models for PDF SOP storage."""

import uuid
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.base import BaseModel, GUID, VectorType
from app.constants import DocumentStatus


class Document(BaseModel):
    """Primary document registry representing an uploaded SOP or manual."""
    __tablename__ = "documents"

    title = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    file_size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=False, unique=True, index=True)
    category = Column(String(100), nullable=True, index=True)      # e.g., Maintenance, Quality, Safety
    department = Column(String(100), nullable=True, index=True)  # e.g., Assembly, CNC, Electrical
    access_scope = Column(String(50), default="public", nullable=False) # public, internal, restricted
    status = Column(String(30), default=DocumentStatus.PENDING.value, nullable=False, index=True)
    metadata_json = Column(JSON, default=dict, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    created_by_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    creator = relationship("User", back_populates="documents")

    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    assets = relationship("DocumentAsset", back_populates="document", cascade="all, delete-orphan")
    ingestion_jobs = relationship("IngestionJob", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document {self.title} status={self.status}>"


class DocumentVersion(BaseModel):
    """Tracks document revision history and change notes."""
    __tablename__ = "document_versions"

    document_id = Column(GUID, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, default=1, nullable=False)
    changelog = Column(Text, nullable=True)
    created_by_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    document = relationship("Document", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
    )


class DocumentPage(BaseModel):
    """Page-level extracted text and layout metadata."""
    __tablename__ = "document_pages"

    document_id = Column(GUID, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    has_ocr = Column(Boolean, default=False, nullable=False)
    page_metadata = Column(JSON, default=dict, nullable=False)

    document = relationship("Document", back_populates="pages")
    chunks = relationship("DocumentChunk", back_populates="page", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("document_id", "page_number", name="uq_doc_page"),
    )


class DocumentChunk(BaseModel):
    """Structure-aware chunk containing text, embedding, and heading hierarchy."""
    __tablename__ = "document_chunks"

    document_id = Column(GUID, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(GUID, ForeignKey("document_pages.id", ondelete="CASCADE"), nullable=True, index=True)
    chunk_index = Column(Integer, nullable=False, index=True)
    section_heading = Column(String(255), nullable=True, index=True)
    subheading = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    parent_chunk_id = Column(GUID, ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    metadata_json = Column(JSON, default=dict, nullable=False)

    # 384-dimensional vector embedding for MiniLM-L6-v2
    embedding = Column(VectorType(384), nullable=True)

    document = relationship("Document", back_populates="chunks")
    page = relationship("DocumentPage", back_populates="chunks")
    parent = relationship("DocumentChunk", remote_side="DocumentChunk.id", backref="children")

    __table_args__ = (
        Index("ix_doc_chunks_doc_active", "document_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk doc={self.document_id} idx={self.chunk_index} tokens={self.token_count}>"


class DocumentAsset(BaseModel):
    """Extracted tables, diagrams, or figures associated with SOP pages."""
    __tablename__ = "document_assets"

    document_id = Column(GUID, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    asset_type = Column(String(50), nullable=False)  # 'table', 'figure', 'image'
    asset_path = Column(String(500), nullable=True)
    caption_or_title = Column(String(255), nullable=True)
    content_json = Column(JSON, default=dict, nullable=False)

    document = relationship("Document", back_populates="assets")

