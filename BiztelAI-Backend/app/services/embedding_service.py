"""Independent vector embedding service supporting local Sentence Transformers."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class BaseEmbeddingProvider(ABC):
    """Abstract interface for embedding generation providers."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Compute normalized vector embeddings for a list of text strings."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Compute normalized vector embedding for a single query."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimension."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return model identifier."""
        pass


class SentenceTransformersProvider(BaseEmbeddingProvider):
    """Local Sentence Transformers embedding provider with batching and L2 normalization."""

    _model_instance = None
    _loaded_model_name = None

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", dimension: int = 384, batch_size: int = 32):
        self._model_name = model_name
        self._dimension = dimension
        self.batch_size = batch_size
        self.model = None  # Lazy loading: do not load during __init__

    def _load_model(self):
        """Lazy-load the transformer model into memory once with local cache prioritization."""
        if SentenceTransformersProvider._model_instance is None or SentenceTransformersProvider._loaded_model_name != self._model_name:
            logger.info("loading_sentence_transformer", model=self._model_name)
            import os
            # Prioritize local cache to avoid slow remote HTTP network checks
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            from sentence_transformers import SentenceTransformer
            try:
                SentenceTransformersProvider._model_instance = SentenceTransformer(self._model_name)
            except Exception as offline_err:
                logger.warning("offline_model_cache_miss_attempting_online", error=str(offline_err))
                # If local cache missing, enable online mode temporarily
                os.environ.pop("HF_HUB_OFFLINE", None)
                os.environ.pop("TRANSFORMERS_OFFLINE", None)
                SentenceTransformersProvider._model_instance = SentenceTransformer(self._model_name)
            SentenceTransformersProvider._loaded_model_name = self._model_name
        self.model = SentenceTransformersProvider._model_instance

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch embed texts with cosine normalization."""
        if not texts:
            return []
        if self.model is None:
            self._load_model()
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,  # Crucial for cosine similarity
            )
            # Validate output dimension
            if len(embeddings) > 0 and len(embeddings[0]) != self._dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self._dimension}, got {len(embeddings[0])}"
                )
            return [e.tolist() for e in embeddings]
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
            raise

    def embed_query(self, query: str) -> List[float]:
        """Embed single search query with normalization."""
        if not query:
            return [0.0] * self._dimension
        result = self.embed_texts([query])
        return result[0]


class EmbeddingService:
    """Service facade providing embedding generation and provider dispatch."""

    def __init__(self, provider: Optional[BaseEmbeddingProvider] = None):
        self.provider = provider or SentenceTransformersProvider()

    def generate_chunk_embeddings(self, chunks: List[Any]) -> List[List[float]]:
        """Extract text from chunks and generate embeddings."""
        texts = [c.content for c in chunks]
        return self.provider.embed_texts(texts)

    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query."""
        return self.provider.embed_query(query)

    @property
    def dimension(self) -> int:
        return self.provider.dimension

    @property
    def model_name(self) -> str:
        return self.provider.model_name
