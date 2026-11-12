"""Tests for Grounding, Hallucination Prevention, and Safe Abstention."""

from app.schemas.response_blocks import (
    CalloutBlock,
    CopilotAnswerResponse,
    MarkdownBlock,
    SourceCitation,
    StepItem,
    StepsBlock,
    StructuredResponse,
)
from app.services.context_service import ContextEngineeringService, EngineeredContext
from app.services.retrieval_service import RetrievedChunk
from app.services.validation_service import ValidationService


def test_validation_detects_invalid_citation():
    validation_service = ValidationService()

    # Context only provides source_1
    citation_1 = SourceCitation(
        id="source_1",
        document_id="doc_1",
        document_title="SOP 1",
        page_number=1,
        snippet="Pneumatic lock pressure is 50 PSI.",
    )
    context = EngineeredContext(
        context_text="...",
        citations=[citation_1],
        citation_map={"source_1": None},
        total_tokens=50,
    )

    # LLM hallucinates source_99
    raw_response = CopilotAnswerResponse(
        answerable=True,
        confidence_score=0.9,
        response=StructuredResponse(
            blocks=[
                StepsBlock(
                    items=[
                        StepItem(id="step_1", content="Check pressure", source_ids=["source_1"]),
                        StepItem(id="step_2", content="Turn valve", source_ids=["source_99"]),  # Invalid citation!
                    ]
                )
            ]
        ),
        sources=[],
        warnings=[],
    )

    validated = validation_service.validate_answer(raw_response, context)
    assert len(validated.unsupported_claims) == 1
    assert "source_99" in validated.unsupported_claims[0]
    assert any("[UNSUPPORTED INSTRUCTION WARNING]" in w for w in validated.warnings)


def test_abstention_on_empty_evidence():
    validation_service = ValidationService()
    empty_context = EngineeredContext(
        context_text="No document evidence.",
        citations=[],
        citation_map={},
        total_tokens=0,
    )

    is_answerable, reason = validation_service.check_answerability(empty_context, "Bake a cake")
    assert is_answerable is False

    abstain_resp = validation_service.create_abstention_response(reason, "Bake a cake")
    assert abstain_resp.answerable is False
    assert abstain_resp.confidence_score == 0.0
    assert len(abstain_resp.response.blocks) >= 1
    assert abstain_resp.response.blocks[0].type == "callout"

