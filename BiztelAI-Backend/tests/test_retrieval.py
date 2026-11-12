"""Tests for hybrid retrieval combining vector similarity, full text, and RRF."""

from app.models.document import Document, DocumentChunk, DocumentPage
from app.services.retrieval_service import RetrievalService, RetrievedChunk


def test_reciprocal_rank_fusion_scoring():
    retrieval = RetrievalService(rrf_k=60)

    # Chunk A: ranked 1 in vector search, ranked 3 in FTS
    chunk_a = RetrievedChunk(
        chunk_id="chunk_a",
        document_id="doc_1",
        document_title="SOP 1",
        page_number=1,
        section_heading="Lockout",
        subheading=None,
        content="Lockout procedure content",
        token_count=100,
        vector_rank=1,
    )

    # Chunk B: ranked 2 in vector search, ranked 1 in FTS
    chunk_b = RetrievedChunk(
        chunk_id="chunk_b",
        document_id="doc_2",
        document_title="SOP 2",
        page_number=1,
        section_heading="Pneumatics",
        subheading=None,
        content="Pneumatic lock pressure",
        token_count=120,
        vector_rank=2,
    )

    vector_candidates = [chunk_a, chunk_b]

    chunk_b_fts = RetrievedChunk(
        chunk_id="chunk_b",
        document_id="doc_2",
        document_title="SOP 2",
        page_number=1,
        section_heading="Pneumatics",
        subheading=None,
        content="Pneumatic lock pressure",
        token_count=120,
        fts_rank=1,
    )
    chunk_a_fts = RetrievedChunk(
        chunk_id="chunk_a",
        document_id="doc_1",
        document_title="SOP 1",
        page_number=1,
        section_heading="Lockout",
        subheading=None,
        content="Lockout procedure content",
        token_count=100,
        fts_rank=3,
    )

    fts_candidates = [chunk_b_fts, chunk_a_fts]

    fused = retrieval._reciprocal_rank_fusion(
        vector_results=vector_candidates,
        fts_results=fts_candidates,
        keyword_results=[],
        top_k=2,
    )

    assert len(fused) == 2
    # chunk_b has rank 2 in vector (1/62) + rank 1 in FTS (1/61) = 0.0161 + 0.0164 = 0.0325
    # chunk_a has rank 1 in vector (1/61) + rank 3 in FTS (1/63) = 0.0164 + 0.0158 = 0.0322
    assert fused[0].chunk_id == "chunk_b"
    assert fused[1].chunk_id == "chunk_a"

