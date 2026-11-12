"""Centralized configuration module with environment validation and Upstash Redis support."""

import os
import sys
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load .env file from project root if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""

    APP_ENV: str = os.getenv("APP_ENV", "development").lower()
    DEBUG: bool = False
    TESTING: bool = False

    # Secrets
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-insecure-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "30"))
    JWT_REFRESH_TOKEN_EXPIRES_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "14"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/biztelai_sop")
    SQLALCHEMY_DATABASE_URI: str = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_pre_ping": True,
    }

    # Upstash Redis & Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    # LLM Multi-provider Configuration
    LLM_API_BASE_URL: str = os.getenv("LLM_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "45"))

    # Embedding & Reranker Configuration
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

    RERANKER_ENABLED: bool = os.getenv("RERANKER_ENABLED", "true").lower() in ("true", "1", "yes")
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "10"))
    RERANK_TOP_K: int = int(os.getenv("RERANK_TOP_K", "5"))
    RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.35"))

    # Document Chunking & Storage
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "700"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    DOCUMENT_STORAGE_PATH: str = os.getenv("DOCUMENT_STORAGE_PATH", str(BASE_DIR / "data" / "documents"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    MAX_CONTENT_LENGTH: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    OCR_ENABLED: bool = os.getenv("OCR_ENABLED", "true").lower() in ("true", "1", "yes")

    # Security & CORS
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://10.200.153.160:5000/api/v1").split(",")
        if origin.strip()
    ]
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")

    @classmethod
    def is_upstash_redis(cls) -> bool:
        """Check if configured Redis URL is an Upstash or TLS-enabled instance."""
        return cls.REDIS_URL.startswith("rediss://") or "upstash.io" in cls.REDIS_URL

    @classmethod
    def get_celery_ssl_options(cls) -> Optional[dict]:
        """Return Celery SSL configuration if TLS/Upstash is detected."""
        if cls.is_upstash_redis():
            import ssl
            return {"ssl_cert_reqs": ssl.CERT_NONE}
        return None

    @classmethod
    def validate(cls, raise_error: bool = True) -> List[str]:
        """Validate mandatory settings and return missing variable names."""
        missing = []
        if not cls.SECRET_KEY or "change-in-production" in cls.SECRET_KEY and cls.APP_ENV == "production":
            missing.append("SECRET_KEY must be a strong unique key in production")
        if not cls.JWT_SECRET_KEY or "change-in-production" in cls.JWT_SECRET_KEY and cls.APP_ENV == "production":
            missing.append("JWT_SECRET_KEY must be a strong unique key in production")
        if not cls.DATABASE_URL:
            missing.append("DATABASE_URL is required")
        if not cls.LLM_API_BASE_URL:
            missing.append("LLM_API_BASE_URL is required")
        if not cls.LLM_MODEL:
            missing.append("LLM_MODEL is required")

        if missing and raise_error:
            error_msg = f"[CRITICAL CONFIGURATION ERROR] Missing or invalid settings:\n" + "\n".join(
                f" - {m}" for m in missing
            )
            raise ValueError(error_msg)
        return missing

    def __repr__(self) -> str:
        """Sanitized representation preventing secret leaks."""
        return (
            f"<Config env={self.APP_ENV} db={self.DATABASE_URL.split('@')[-1] if '@' in self.DATABASE_URL else 'masked'} "
            f"llm_model={self.LLM_MODEL} embedding={self.EMBEDDING_MODEL}>"
        )


class DevelopmentConfig(Config):
    """Development configuration with debugging enabled."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration with in-memory or test database and mocked services."""
    TESTING = True
    DEBUG = True
    APP_ENV = "testing"
    DATABASE_URL = "sqlite:///:memory:"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    REDIS_URL = "redis://localhost:6379/15"
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND = "cache+memory://"
    DOCUMENT_STORAGE_PATH = str(BASE_DIR / "data" / "test_documents")
    RERANKER_ENABLED = False  # Keep test execution fast by default


class ProductionConfig(Config):
    """Strict production configuration."""
    DEBUG = False
    TESTING = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env_name: Optional[str] = None) -> type[Config]:
    """Retrieve configuration class based on environment name."""
    env = (env_name or os.getenv("APP_ENV", "development")).lower()
    return CONFIG_MAP.get(env, DevelopmentConfig)

