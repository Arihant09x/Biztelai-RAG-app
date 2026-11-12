"""Hybrid retrieval service combining pgvector similarity, PostgreSQL FTS, and RRF."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
from sqlalchemy import and_, or_, text
from app.extensions import db
from app.models.document import Document, DocumentChunk, DocumentPage
from app.services.embedding_service import EmbeddingService
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_title: str
    page_number: int
    section_heading: Optional[str]
    subheading: Optional[str]
    content: str
    token_count: int
    vector_rank: Optional[int] = None
    fts_rank: Optional[int] = None
    keyword_rank: Optional[int] = None
    similarity_score: float = 0.0
    rrf_score: float = 0.0
    category: Optional[str] = None
    department: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RetrievalService:
    """Hybrid search orchestrator executing vector search, full-text search, and RRF fusion."""

    def __init__(self, embedding_service: Optional[EmbeddingService] = None, rrf_k: int = 60):
        self._embedding_service = embedding_service
        self.rrf_k = rrf_k

    @property
    def embedding_service(self) -> EmbeddingService:
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        category: Optional[str] = None,
        department: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        access_scopes: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        """Perform multi-channel hybrid search and combine candidates via Reciprocal Rank Fusion."""
        if not query or not query.strip():
            return []

        # 1. Generate query embedding
        query_vector = self.embedding_service.generate_query_embedding(query)

        # 2. Vector Search Candidates
        vector_results = self._vector_search(
            query_vector,
            limit=top_k * 2,
            category=category,
            department=department,
            document_ids=document_ids,
            access_scopes=access_scopes,
        )

        # 3. Full-Text Search Candidates
        fts_results = self._fts_search(
            query,
            limit=top_k * 2,
            category=category,
            department=department,
            document_ids=document_ids,
            access_scopes=access_scopes,
        )

        # 4. Keyword / Code exact matches (e.g. machine models, error codes, SOP numbers)
        keyword_results = self._exact_keyword_search(
            query,
            limit=top_k * 2,
            category=category,
            department=department,
            document_ids=document_ids,
            access_scopes=access_scopes,
        )

        # 5. Reciprocal Rank Fusion (RRF)
        fused_chunks = self._reciprocal_rank_fusion(
            vector_results=vector_results,
            fts_results=fts_results,
            keyword_results=keyword_results,
            top_k=top_k,
        )

        return fused_chunks

    def _vector_search(
        self,
        query_vector: List[float],
        limit: int,
        category: Optional[str] = None,
        department: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        access_scopes: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        """Execute vector similarity search using pgvector or in-memory cosine fallback."""
        dialect_name = db.engine.dialect.name
        results: List[RetrievedChunk] = []

        query_filter = [
            DocumentChunk.is_active.is_(True),
            Document.is_deleted.is_(False),
        ]
        if category:
            query_filter.append(Document.category == category)
        if department:
            query_filter.append(Document.department == department)
        if document_ids:
            query_filter.append(Document.id.in_(document_ids))
        if access_scopes:
            query_filter.append(Document.access_scope.in_(access_scopes))

        # Ensure query_vector is a clean 1-dimensional float32 numpy array
        q_vec = np.asarray(query_vector, dtype=np.float32).flatten()

        if dialect_name == "postgresql":
            try:
                # Format vector directly into PostgreSQL vector literal to avoid psycopg ndim serialization bugs
                from sqlalchemy import literal_column
                vec_str = "[" + ",".join(f"{float(x):.6f}" for x in q_vec.tolist()) + "]"
                vec_expr = literal_column(f"'{vec_str}'::vector")
                dist_expr = DocumentChunk.embedding.op("<=>")(vec_expr)

                chunks = (
                    db.session.query(
                        DocumentChunk,
                        Document,
                        DocumentPage.page_number,
                        (1.0 - dist_expr).label("sim_score"),
                    )
                    .join(Document, DocumentChunk.document_id == Document.id)
                    .outerjoin(DocumentPage, DocumentChunk.page_id == DocumentPage.id)
                    .filter(*query_filter)
                    .order_by(dist_expr)
                    .limit(limit)
                    .all()
                )

                for rank, (c, doc, p_num, sim) in enumerate(chunks, start=1):
                    results.append(
                        RetrievedChunk(
                            chunk_id=str(c.id),
                            document_id=str(doc.id),
                            document_title=doc.title,
                            page_number=p_num or 1,
                            section_heading=c.section_heading,
                            subheading=c.subheading,
                            content=c.content,
                            token_count=c.token_count,
                            vector_rank=rank,
                            similarity_score=float(sim or 0.0),
                            category=doc.category,
                            department=doc.department,
                            metadata=c.metadata_json,
                        )
                    )
                return results
            except Exception as e:
                logger.warning("pgvector_native_search_fallback", error=str(e))

        # Dialect fallback (SQLite / Python-level cosine similarity)
        chunks = (
            db.session.query(DocumentChunk, Document, DocumentPage.page_number)
            .join(Document, DocumentChunk.document_id == Document.id)
            .outerjoin(DocumentPage, DocumentChunk.page_id == DocumentPage.id)
            .filter(*query_filter)
            .all()
        )

        q_norm = float(np.linalg.norm(q_vec))
        scored: List[tuple] = []

        for c, doc, p_num in chunks:
            c_emb = c.embedding
            if c_emb is not None:
                if isinstance(c_emb, list):
                    v = np.array(c_emb, dtype=np.float32)
                else:
                    v = np.array(c_emb, dtype=np.float32)
                v_norm = np.linalg.norm(v)
                if q_norm > 0 and v_norm > 0:
                    sim = float(np.dot(q_vec, v) / (q_norm * v_norm))
                else:
                    sim = 0.0
                scored.append((sim, c, doc, p_num))

        scored.sort(key=lambda x: x[0], reverse=True)
        for rank, (sim, c, doc, p_num) in enumerate(scored[:limit], start=1):
            results.append(
                RetrievedChunk(
                    chunk_id=str(c.id),
                    document_id=str(doc.id),
                    document_title=doc.title,
                    page_number=p_num or 1,
                    section_heading=c.section_heading,
                    subheading=c.subheading,
                    content=c.content,
                    token_count=c.token_count,
                    vector_rank=rank,
                    similarity_score=sim,
                    category=doc.category,
                    department=doc.department,
                    metadata=c.metadata_json,
                )
            )

        return results

    def _fts_search(
        self,
        query: str,
        limit: int,
        category: Optional[str] = None,
        department: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        access_scopes: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        """Execute full-text search against chunk contents."""
        results: List[RetrievedChunk] = []
        dialect_name = db.engine.dialect.name

        query_filter = [
            DocumentChunk.is_active.is_(True),
            Document.is_deleted.is_(False),
        ]
        if category:
            query_filter.append(Document.category == category)
        if department:
            query_filter.append(Document.department == department)
        if document_ids:
            query_filter.append(Document.id.in_(document_ids))
        if access_scopes:
            query_filter.append(Document.access_scope.in_(access_scopes))

        # Query words
        terms = [t for t in query.split() if len(t) > 2]
        if not terms:
            return []

        if dialect_name == "postgresql":
            try:
                # Use PostgreSQL plainto_tsquery or websearch_to_tsquery
                ts_query = " & ".join(terms)
                chunks = (
                    db.session.query(DocumentChunk, Document, DocumentPage.page_number)
                    .join(Document, DocumentChunk.document_id == Document.id)
                    .outerjoin(DocumentPage, DocumentChunk.page_id == DocumentPage.id)
                    .filter(
                        *query_filter,
                        text("to_tsvector('english', document_chunks.content) @@ plainto_tsquery('english', :query)"),
                    )
                    .params(query=query)
                    .limit(limit)
                    .all()
                )
                for rank, (c, doc, p_num) in enumerate(chunks, start=1):
                    results.append(
                        RetrievedChunk(
                            chunk_id=str(c.id),
                            document_id=str(doc.id),
                            document_title=doc.title,
                            page_number=p_num or 1,
                            section_heading=c.section_heading,
                            subheading=c.subheading,
                            content=c.content,
                            token_count=c.token_count,
                            fts_rank=rank,
                            category=doc.category,
                            department=doc.department,
                            metadata=c.metadata_json,
                        )
                    )
                return results
            except Exception as e:
                logger.warning("postgresql_fts_fallback", error=str(e))

        # Fallback ILIKE / keyword matching
        conditions = [DocumentChunk.content.ilike(f"%{term}%") for term in terms]
        chunks = (
            db.session.query(DocumentChunk, Document, DocumentPage.page_number)
            .join(Document, DocumentChunk.document_id == Document.id)
            .outerjoin(DocumentPage, DocumentChunk.page_id == DocumentPage.id)
            .filter(*query_filter, or_(*conditions))
            .limit(limit)
            .all()
        )

        for rank, (c, doc, p_num) in enumerate(chunks, start=1):
            results.append(
                RetrievedChunk(
                    chunk_id=str(c.id),
                    document_id=str(doc.id),
                    document_title=doc.title,
                    page_number=p_num or 1,
                    section_heading=c.section_heading,
                    subheading=c.subheading,
                    content=c.content,
                    token_count=c.token_count,
                    fts_rank=rank,
                    category=doc.category,
                    department=doc.department,
                    metadata=c.metadata_json,
                )
            )

        return results

    def _exact_keyword_search(
        self,
        query: str,
        limit: int,
        category: Optional[str] = None,
        department: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        access_scopes: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        """Detect and match exact manufacturing codes, error strings, and equipment numbers."""
        import re

        # Extract codes like "SOP-104", "CNC-500", "E-204", "ISO-9001"
        codes = re.findall(r"\b[A-Za-z0-9]+-[A-Za-z0-9]+\b|\b[A-Z]{2,}\d+\b", query)
        if not codes:
            return []

        results: List[RetrievedChunk] = []
        query_filter = [
            DocumentChunk.is_active.is_(True),
            Document.is_deleted.is_(False),
        ]
        if category:
            query_filter.append(Document.category == category)
        if department:
            query_filter.append(Document.department == department)
        if document_ids:
            query_filter.append(Document.id.in_(document_ids))
        if access_scopes:
            query_filter.append(Document.access_scope.in_(access_scopes))

        conditions = [DocumentChunk.content.ilike(f"%{code}%") for code in codes]
        chunks = (
            db.session.query(DocumentChunk, Document, DocumentPage.page_number)
            .join(Document, DocumentChunk.document_id == Document.id)
            .outerjoin(DocumentPage, DocumentChunk.page_id == DocumentPage.id)
            .filter(*query_filter, or_(*conditions))
            .limit(limit)
            .all()
        )

        for rank, (c, doc, p_num) in enumerate(chunks, start=1):
            results.append(
                RetrievedChunk(
                    chunk_id=str(c.id),
                    document_id=str(doc.id),
                    document_title=doc.title,
                    page_number=p_num or 1,
                    section_heading=c.section_heading,
                    subheading=c.subheading,
                    content=c.content,
                    token_count=c.token_count,
                    keyword_rank=rank,
                    category=doc.category,
                    department=doc.department,
                    metadata=c.metadata_json,
                )
            )

        return results

    @staticmethod
    def _extract_revision_metadata(text_str: str) -> Tuple[Optional[str], Optional[int], bool]:
        """Extract SOP document family code, revision number, and whether it supersedes an earlier revision.

        Returns:
            (doc_family, revision_number, has_superseded_claim)
            e.g. ("QC-SOP-014", 4, True)
        """
        doc_family = None
        family_match = re.search(r"([A-Z]{2,4}-SOP-\d+|SOP-\d+|MNT-MAN-[A-Z]+-\d+)(?=[^A-Za-z0-9]|$)", text_str, re.IGNORECASE)
        if family_match:
            doc_family = family_match.group(1).upper()

        rev_num = None
        rev_match = re.search(r"(?:Rev|Revision)\s*[:\-_]?\s*0*(\d+)(?=[^A-Za-z0-9]|$)", text_str, re.IGNORECASE)
        if rev_match:
            try:
                rev_num = int(rev_match.group(1))
            except ValueError:
                pass

        has_superseded = bool(re.search(r"\bsupersedes\s+rev(?:ision)?\b", text_str, re.IGNORECASE))
        return doc_family, rev_num, has_superseded

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[RetrievedChunk],
        fts_results: List[RetrievedChunk],
        keyword_results: List[RetrievedChunk],
        top_k: int,
    ) -> List[RetrievedChunk]:
        """Combine ranks across channels using Reciprocal Rank Fusion with ISO 9001 revision prioritization."""
        all_by_id: Dict[str, RetrievedChunk] = {}
        rrf_scores: Dict[str, float] = {}

        for chunk in vector_results:
            cid = chunk.chunk_id
            all_by_id[cid] = chunk
            rank = chunk.vector_rank or 999
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        for chunk in fts_results:
            cid = chunk.chunk_id
            if cid not in all_by_id:
                all_by_id[cid] = chunk
            rank = chunk.fts_rank or 999
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        for chunk in keyword_results:
            cid = chunk.chunk_id
            if cid not in all_by_id:
                all_by_id[cid] = chunk
            rank = chunk.keyword_rank or 999
            # Boost exact keyword matches
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.2 / (self.rrf_k + rank))

        # ISO 9001 Revision Intelligence:
        # Determine highest revision per document family across all retrieved candidates
        family_max_rev: Dict[str, int] = {}
        for chunk in all_by_id.values():
            fam, rev, _ = self._extract_revision_metadata(f"{chunk.document_title} {chunk.content}")
            if fam and rev is not None:
                family_max_rev[fam] = max(family_max_rev.get(fam, 0), rev)

        # Apply ISO 9001 revision recency boost / obsolete penalty
        for cid, chunk in all_by_id.items():
            fam, rev, supersedes = self._extract_revision_metadata(f"{chunk.document_title} {chunk.content}")
            if fam and rev is not None and fam in family_max_rev:
                if rev == family_max_rev[fam]:
                    # Active latest revision boost (+0.05 score boost)
                    rrf_scores[cid] += 0.05
                    if supersedes:
                        rrf_scores[cid] += 0.02
                elif rev < family_max_rev[fam]:
                    # Obsolete revision down-weight
                    rrf_scores[cid] = max(0.001, rrf_scores[cid] - 0.03)

        # Assign RRF score and sort
        for cid, score in rrf_scores.items():
            all_by_id[cid].rrf_score = score

        sorted_chunks = sorted(all_by_id.values(), key=lambda c: c.rrf_score, reverse=True)
        return sorted_chunks[:top_k]
