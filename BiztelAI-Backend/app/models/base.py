"""Database base model, UUID helper, and cross-dialect Vector column support."""

import uuid
from datetime import datetime, timezone
import json
from sqlalchemy import DateTime, String, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.extensions import db


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type.
    Uses PostgreSQL's native UUID type, otherwise uses CHAR(36).
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class VectorType(TypeDecorator):
    """Cross-dialect Vector column support.
    Uses pgvector's Vector(dim) on PostgreSQL, and JSON-encoded array on SQLite/others.
    """
    impl = String
    cache_ok = True

    def __init__(self, dim: int = 384, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dim))
            except ImportError:
                pass
        # Fallback to Text/String for SQLite in-memory testing
        return dialect.type_descriptor(db.Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        import numpy as np
        if dialect.name == "postgresql":
            if isinstance(value, np.ndarray):
                return value.astype(np.float32).flatten()
            if isinstance(value, (list, tuple)):
                return np.asarray(value, dtype=np.float32).flatten()
            return value
        if isinstance(value, (list, tuple, np.ndarray)):
            if hasattr(value, "tolist"):
                return json.dumps(value.tolist())
            return json.dumps(list(value))
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        if hasattr(value, "tolist"):
            return value.tolist()
        return value


class BaseModel(db.Model):
    """Abstract base model with UUID primary key and timestamp audit columns."""
    __abstract__ = True

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    created_at = db.Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = db.Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

