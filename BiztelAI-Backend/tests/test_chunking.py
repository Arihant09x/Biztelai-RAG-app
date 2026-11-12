"""Tests for structure-aware chunking of manufacturing documents."""

from app.services.chunking_service import ChunkingService
from app.services.pdf_extraction_service import ExtractedPage, ExtractedTable


def test_chunking_preserves_headings_and_safety_warnings():
    chunker = ChunkingService(target_chunk_tokens=300, overlap_tokens=50)

    text = (
        "SECTION 1: ELECTRICAL ISOLATION\n\n"
        "[SAFETY WARNING]\n"
        "DANGER: 480V Hazard. Disconnect main breaker before removing terminal covers.\n\n"
        "1. Turn off local switch.\n"
        "2. Affix red padlock.\n"
        "3. Verify zero voltage with multimeter."
    )

    page = ExtractedPage(
        page_number=1,
        text=text,
        headings=["SECTION 1: ELECTRICAL ISOLATION"],
    )

    chunks = chunker.chunk_document(
        pages=[page],
        document_id="doc-123",
        document_title="Electrical Safety SOP",
        category="Safety",
        department="Electrical",
    )

    assert len(chunks) >= 1
    c0 = chunks[0]
    assert c0.page_number == 1
    assert "SECTION 1" in (c0.section_heading or "")
    assert c0.metadata["has_safety_warning"] is True
    assert c0.metadata["is_procedure"] is True
    assert "480V Hazard" in c0.content


def test_chunking_with_tables():
    chunker = ChunkingService(target_chunk_tokens=500, overlap_tokens=50)

    table = ExtractedTable(
        page_number=1,
        headers=["Component", "Torque Spec", "Tolerance"],
        rows=[["Spindle Bolt", "45 Nm", "±2 Nm"], ["Flange Nut", "30 Nm", "±1 Nm"]],
        title="Torque Specifications",
    )

    page = ExtractedPage(
        page_number=1,
        text="Standard torque specification table for machine assembly.",
        tables=[table],
    )

    chunks = chunker.chunk_document([page], "doc-456", "Assembly Guide")
    assert len(chunks) >= 1
    assert "| Spindle Bolt | 45 Nm | ±2 Nm |" in chunks[0].content

