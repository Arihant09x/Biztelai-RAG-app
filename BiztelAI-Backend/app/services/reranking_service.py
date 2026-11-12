"""Cross-encoder reranking service with calibration and graceful fallback."""

import time
from typing import List, Optional, Tuple
from app.services.retrieval_service import RetrievedChunk
import structlog

logger = structlog.get_logger(__name__)


class RerankingService:
    """Reranks initial candidate chunks using a neural Cross-Encoder model."""

    _model_instance = None
    _loaded_model_name = None

    def __init__(
        self,
        model_name: Optional[str] = None,
        enabled: Optional[bool] = None,
        threshold: Optional[float] = None,
    ):
        from flask import current_app
        if current_app:
            self.enabled = current_app.config.get("RERANKER_ENABLED", False) if enabled is None else enabled
            self.model_name = current_app.config.get("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2") if model_name is None else model_name
            self.threshold = current_app.config.get("RAG_SIMILARITY_THRESHOLD", 0.35) if threshold is None else threshold
        else:
            self.enabled = False if enabled is None else enabled
            self.model_name = model_name or "cross-encoder/ms-marco-MiniLM-L-6-v2"
            self.threshold = threshold if threshold is not None else 0.35

        if self.enabled:
            self._init_model()

    def _init_model(self):
        """Lazy-load the CrossEncoder model into memory."""
        if not self.enabled:
            return
        if RerankingService._model_instance is None or RerankingService._loaded_model_name != self.model_name:
            try:
                import os
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
                from sentence_transformers import CrossEncoder
                logger.info("loading_reranker_model", model=self.model_name)
                try:
                    RerankingService._model_instance = CrossEncoder(self.model_name)
                except Exception:
                    os.environ.pop("HF_HUB_OFFLINE", None)
                    os.environ.pop("TRANSFORMERS_OFFLINE", None)
                    RerankingService._model_instance = CrossEncoder(self.model_name)
                RerankingService._loaded_model_name = self.model_name
            except Exception as e:
                logger.warning("reranker_initialization_failed_fallback_disabled", error=str(e))
                self.enabled = False

    def rerank(
        self,
        query: str,
        candidates: List[RetrievedChunk],
        top_k: int = 5,
    ) -> Tuple[List[RetrievedChunk], float]:
        """Rerank candidates and filter out low-confidence evidence below threshold.

        Returns:
            Tuple[reranked_chunks, rerank_latency_ms]
        """
        start_time = time.time()
        if not candidates or not query:
            return [], 0.0

        # Deduplicate candidates by chunk_id
        unique_candidates: List[RetrievedChunk] = []
        seen_ids = set()
        for c in candidates:
            if c.chunk_id not in seen_ids:
                seen_ids.add(c.chunk_id)
                unique_candidates.append(c)

        if not self.enabled or RerankingService._model_instance is None:
            # Fallback: Sort by existing RRF / similarity score
            duration_ms = round((time.time() - start_time) * 1000, 2)
            filtered = [c for c in unique_candidates if c.similarity_score >= self.threshold or c.rrf_score > 0]
            return filtered[:top_k], duration_ms

        try:
            # Prepare query-document pairs
            pairs = [[query, f"{c.section_heading or ''}\n{c.content}"] for c in unique_candidates]
            scores = RerankingService._model_instance.predict(pairs)

            # Assign cross-encoder scores (apply sigmoid if necessary to map to [0, 1])
            scored_candidates = []
            for chunk, raw_score in zip(unique_candidates, scores):
                calibrated_score = float(1.0 / (1.0 + (2.71828 ** -raw_score)))  # sigmoid calibration
                chunk.similarity_score = calibrated_score
                if calibrated_score >= self.threshold:
                    scored_candidates.append((calibrated_score, chunk))

            # Sort descending by cross-encoder score
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            reranked = [c for _, c in scored_candidates[:top_k]]
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return reranked, duration_ms

        except Exception as e:
            logger.error("reranking_execution_failed_falling_back", error=str(e))
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return unique_candidates[:top_k], duration_ms
