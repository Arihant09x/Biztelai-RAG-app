"""Embedding model metadata and index version tracking."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.extensions import db
from app.models.base import BaseModel, GUID


class EmbeddingModel(BaseModel):
    """Tracks registered vector embedding models to avoid incompatible dimension collisions."""
    __tablename__ = "embedding_models"

    name = Column(String(100), unique=True, nullable=False, index=True)
    dimension = Column(Integer, nullable=False)
    provider = Column(String(50), default="sentence_transformers", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    index_versions = relationship("IndexVersion", back_populates="embedding_model", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<EmbeddingModel {self.name} dim={self.dimension}>"


class IndexVersion(BaseModel):
    """Tracks versioned vector collections to trigger fresh re-indexing on model change."""
    __tablename__ = "index_versions"

    embedding_model_id = Column(GUID, ForeignKey("embedding_models.id", ondelete="CASCADE"), nullable=False, index=True)
    version_tag = Column(String(50), nullable=False)  # e.g., 'v1.0-minilm'
    total_chunks = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    embedding_model = relationship("EmbeddingModel", back_populates="index_versions")

    def __repr__(self) -> str:
        return f"<IndexVersion tag={self.version_tag} model={self.embedding_model_id}>"

