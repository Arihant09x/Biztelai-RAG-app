"""Unit tests for Pydantic v2 structured response blocks."""

import pytest
from pydantic import ValidationError
from app.schemas.response_blocks import (
    CalloutBlock,
    ChecklistBlock,
    ChecklistItem,
    ComparisonBlock,
    ComparisonItem,
    CopilotAnswerResponse,
    MarkdownBlock,
    MermaidBlock,
    SourceCitation,
    StepItem,
    StepsBlock,
    StructuredResponse,
    TableBlock,
)


def test_markdown_block_valid():
    block = MarkdownBlock(type="markdown", content="Valid text content.")
    assert block.type == "markdown"
    assert block.content == "Valid text content."


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        # Disallows arbitrary extra keys like HTML or script injections
        MarkdownBlock(type="markdown", content="Hi", malicious_field="<script>alert(1)</script>")


def test_callout_block_variants():
    valid_callout = CalloutBlock(
        type="callout",
        variant="warning",
        title="Safety Alert",
        content="Wear protective goggles.",
        source_ids=["source_1"],
    )
    assert valid_callout.variant == "warning"

    with pytest.raises(ValidationError):
        # Invalid variant name
        CalloutBlock(type="callout", variant="invalid_variant", content="text")


def test_steps_block_validation():
    steps = StepsBlock(
        type="steps",
        title="Maintenance Steps",
        items=[
            StepItem(id="step_1", content="Disconnect 480V breaker.", source_ids=["source_1"]),
            StepItem(id="step_2", content="Verify zero voltage.", source_ids=["source_1", "source_2"]),
        ],
    )
    assert len(steps.items) == 2
    assert steps.items[0].id == "step_1"


def test_mermaid_block_validation():
    valid_chart = MermaidBlock(
        type="mermaid",
        title="Process Flow",
        chart="flowchart TD\n  A[Start] --> B[Shutdown]\n  B --> C[Verify]",
    )
    assert "flowchart TD" in valid_chart.chart

    with pytest.raises(ValidationError):
        # Must start with allowed diagram syntax
        MermaidBlock(type="mermaid", chart="<script>malicious</script>")


def test_table_block_validation():
    table = TableBlock(
        type="table",
        title="Operating Parameters",
        headers=["Parameter", "Standard", "Tolerance"],
        rows=[
            ["Hydraulic Pressure", "180 bar", "±5 bar"],
            ["Coolant Temp", "20°C", "±2°C"],
        ],
    )
    assert len(table.headers) == 3
    assert len(table.rows) == 2


def test_full_copilot_answer_response():
    resp = CopilotAnswerResponse(
        answerable=True,
        confidence_score=0.92,
        response=StructuredResponse(
            blocks=[
                MarkdownBlock(content="Summary of spindle procedure."),
                CalloutBlock(variant="warning", content="Ensure pneumatic lock at 50 PSI.", source_ids=["source_1"]),
            ]
        ),
        sources=[
            SourceCitation(
                id="source_1",
                document_id="doc-123",
                document_title="CNC Spindle Manual",
                page_number=1,
                snippet="Maintain pneumatic lock at 50 PSI.",
                relevance_score=0.94,
            )
        ],
        warnings=[],
    )
    assert resp.answerable is True
    assert len(resp.response.blocks) == 2
    assert len(resp.sources) == 1

