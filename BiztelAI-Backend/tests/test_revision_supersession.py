"""Tests for ISO 9001 document revision supersession edge case."""

from app.schemas.response_blocks import CalloutBlock, ContentBlock, CopilotAnswerResponse, MarkdownBlock, StructuredResponse
from app.services.context_service import ContextEngineeringService
from app.services.retrieval_service import RetrievalService, RetrievedChunk
from app.services.validation_service import ValidationService


def test_revision_metadata_extraction():
    retrieval = RetrievalService()

    fam, rev, sup = retrieval._extract_revision_metadata("QC-SOP-014_Rev03_Incoming_Material_Inspection.pdf")
    assert fam == "QC-SOP-014"
    assert rev == 3
    assert not sup

    fam, rev, sup = retrieval._extract_revision_metadata(
        "QC-SOP-014 Rev 04 Effective 01-Jul-2026 Supersedes Rev 03. Lot-size based sampling plan."
    )
    assert fam == "QC-SOP-014"
    assert rev == 4
    assert sup is True


def test_reciprocal_rank_fusion_prioritizes_latest_revision():
    retrieval = RetrievalService(rrf_k=60)

    # Chunk from Rev 03 (ranked 1 initially in vector)
    chunk_rev3 = RetrievedChunk(
        chunk_id="chunk_rev3",
        document_id="doc_rev3",
        document_title="QC-SOP-014 Rev 03 Incoming Inspection",
        page_number=1,
        section_heading="Procedure",
        subheading=None,
        content="Draw 5 samples from every lot. Keep rejected parts in Red Bin near Gate 2.",
        token_count=100,
        vector_rank=1,
    )

    # Chunk from Rev 04 (ranked 2 initially in vector)
    chunk_rev4 = RetrievedChunk(
        chunk_id="chunk_rev4",
        document_id="doc_rev4",
        document_title="QC-SOP-014 Rev 04 Incoming Inspection",
        page_number=1,
        section_heading="Sampling Plan",
        subheading=None,
        content="Supersedes Rev 03. Lot-size based sampling plan. Quarantine in locked Cage Q1. Outer diameter 90.000 +/- 0.050 mm.",
        token_count=100,
        vector_rank=2,
    )

    fused = retrieval._reciprocal_rank_fusion(
        vector_results=[chunk_rev3, chunk_rev4],
        fts_results=[],
        keyword_results=[],
        top_k=2,
    )

    assert len(fused) == 2
    # Even though Rev 03 had vector_rank=1, Rev 04 receives ISO 9001 revision boost (+0.05 + 0.02 supersedes)
    # and Rev 03 receives obsolete down-weight (-0.03), making Rev 04 the top ranked evidence!
    assert fused[0].chunk_id == "chunk_rev4"
    assert fused[1].chunk_id == "chunk_rev3"


def test_context_engineering_detects_supersession_and_tags_evidence():
    context_svc = ContextEngineeringService()

    chunk_rev3 = RetrievedChunk(
        chunk_id="c3",
        document_id="doc_rev3",
        document_title="QC-SOP-014 Rev 03 Incoming Inspection",
        page_number=1,
        section_heading="Procedure",
        subheading=None,
        content="Sample size 5 for all lots.",
        token_count=50,
        similarity_score=0.75,
    )

    chunk_rev4 = RetrievedChunk(
        chunk_id="c4",
        document_id="doc_rev4",
        document_title="QC-SOP-014 Rev 04 Incoming Inspection",
        page_number=2,
        section_heading="BH-220 Dimensions",
        subheading=None,
        content="Supersedes Rev 03. Outer diameter 90.000 +/- 0.050 mm.",
        token_count=50,
        similarity_score=0.85,
    )

    context = context_svc.engineer_context(
        chunks=[chunk_rev3, chunk_rev4],
        query="What is the outer diameter tolerance for BH-220?",
    )

    # 1. Contradiction / Supersession warning must be registered
    assert any("ISO 9001 SUPERSEDED REVISION DETECTED" in c for c in context.contradictions_detected)

    # 2. Context text must tag Rev 04 as ACTIVE and Rev 03 as OBSOLETE
    assert "ACTIVE APPROVED REVISION 04" in context.context_text
    assert "OBSOLETE / SUPERSEDED" in context.context_text


def test_validation_service_enforces_iso9001_callout():
    validation_svc = ValidationService()
    context_svc = ContextEngineeringService()

    chunk_rev3 = RetrievedChunk(
        chunk_id="c3",
        document_id="doc_rev3",
        document_title="QC-SOP-014 Rev 03 Incoming Inspection",
        page_number=1,
        section_heading="Procedure",
        subheading=None,
        content="Sample size 5 for all lots.",
        token_count=50,
        similarity_score=0.75,
    )
    chunk_rev4 = RetrievedChunk(
        chunk_id="c4",
        document_id="doc_rev4",
        document_title="QC-SOP-014 Rev 04 Incoming Inspection",
        page_number=2,
        section_heading="BH-220 Dimensions",
        subheading=None,
        content="Supersedes Rev 03. Outer diameter 90.000 +/- 0.050 mm.",
        token_count=50,
        similarity_score=0.85,
    )

    context = context_svc.engineer_context(
        chunks=[chunk_rev3, chunk_rev4],
        query="What is the outer diameter for BH-220?",
    )

    # Raw response from LLM that forgot the warning callout
    raw_response = CopilotAnswerResponse(
        answerable=True,
        confidence_score=0.92,
        response=StructuredResponse(
            blocks=[
                MarkdownBlock(type="markdown", content="The outer diameter is 90.000 +/- 0.050 mm."),
            ]
        ),
        sources=[],
        warnings=[],
    )

    validated = validation_svc.validate_answer(raw_response, context)

    # Validation service must inject the ISO 9001 Obsolete Revision Alert callout
    assert any(b.type == "callout" and "ISO 9001" in getattr(b, "title", "") for b in validated.response.blocks)

