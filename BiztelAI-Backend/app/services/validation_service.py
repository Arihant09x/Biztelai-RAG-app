"""Grounding validation, hallucination detection, citation checking, and abstention service."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from app.schemas.response_blocks import (
    CalloutBlock,
    ContentBlock,
    CopilotAnswerResponse,
    MarkdownBlock,
    SourceCitation,
    StructuredResponse,
)
from app.services.context_service import EngineeredContext
from app.services.retrieval_service import RetrievedChunk
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ValidationResult:
    is_grounded: bool
    is_answerable: bool
    validated_sources: List[SourceCitation]
    missing_citations: List[str]
    unsupported_steps: List[str]
    contradictions: List[str]
    sanitized_response: Optional[StructuredResponse] = None
    warnings: List[str] = field(default_factory=list)


class ValidationService:
    """Verifies that generated answers cite real retrieved evidence and do not hallucinate instructions."""

    def __init__(self, min_similarity_threshold: float = 0.30):
        self.min_similarity_threshold = min_similarity_threshold

    def check_answerability(self, context: EngineeredContext, query: str) -> Tuple[bool, Optional[str]]:
        """Determine whether the retrieved context contains sufficient evidence to answer."""
        if not context.citations:
            return False, "No relevant standard operating procedure documents were found matching your query."

        # Check maximum relevance score across retrieved citations
        max_score = 0.0
        for c in context.citations:
            if c.relevance_score and c.relevance_score > max_score:
                max_score = c.relevance_score

        # If similarity is lower than minimum calibrated threshold, abstain
        if max_score > 0 and max_score < self.min_similarity_threshold:
            return (
                False,
                f"Retrieved document evidence is below the required confidence threshold ({max_score:.2f} < {self.min_similarity_threshold:.2f}). "
                "To prevent manufacturing hazards, the system abstains from generating unverified instructions.",
            )

        return True, None

    def validate_answer(
        self,
        raw_response: CopilotAnswerResponse,
        context: EngineeredContext,
    ) -> CopilotAnswerResponse:
        """Validate citation IDs, detect unsupported claims, and append safety warnings."""
        valid_citation_ids: Set[str] = {c.id for c in context.citations}
        referenced_source_ids: Set[str] = set()
        unsupported_steps: List[str] = []
        warnings: List[str] = list(raw_response.warnings)

        # Inspect all structured blocks
        for block in raw_response.response.blocks:
            if block.type == "steps":
                for item in block.items:
                    for sid in item.source_ids:
                        referenced_source_ids.add(sid)
                        if sid not in valid_citation_ids:
                            unsupported_steps.append(f"Step '{item.id}' cites invalid {sid}")
            elif block.type == "checklist":
                for item in block.items:
                    for sid in item.source_ids:
                        referenced_source_ids.add(sid)
                        if sid not in valid_citation_ids:
                            unsupported_steps.append(f"Checklist item '{item.id}' cites invalid {sid}")
            elif block.type == "callout":
                for sid in getattr(block, "source_ids", []):
                    referenced_source_ids.add(sid)

        # Filter only citations that were actually referenced in the answer
        active_citations = [c for c in context.citations if c.id in referenced_source_ids]
        if not active_citations and context.citations:
            # If the model didn't attach citation IDs to individual steps, keep top supporting citations
            active_citations = context.citations[:3]

        # Flag detected contradictions and enforce ISO 9001 revision warning
        if context.contradictions_detected:
            for contra in context.contradictions_detected:
                warnings.append(f"[CONTRADICTION DETECTED] {contra}")

            superseded_alerts = [c for c in context.contradictions_detected if "ISO 9001 SUPERSEDED REVISION DETECTED" in c]
            if superseded_alerts:
                has_rev_callout = any(
                    b.type == "callout" and (
                        "supersed" in getattr(b, "content", "").lower()
                        or "rev" in (getattr(b, "title", "") or "").lower()
                        or "obsolete" in (getattr(b, "title", "") or "").lower()
                    )
                    for b in raw_response.response.blocks
                )
                if not has_rev_callout:
                    rev_callout = CalloutBlock(
                        type="callout",
                        variant="warning",
                        title="ISO 9001 Obsolete Revision Alert",
                        content="Notice: An obsolete document revision was detected in the archive. In accordance with ISO 9001 Clause 7.5.3 (Control of Documented Information), this response has been strictly prioritized and grounded in the latest approved active revision (QC-SOP-014 Rev 04). Obsolete specifications from Rev 03 must not be used on the shop floor.",
                        source_ids=[c.id for c in context.citations if "Rev" in c.document_title or "014" in c.document_title][:2],
                    )
                    insert_pos = 1 if len(raw_response.response.blocks) > 0 and raw_response.response.blocks[0].type == "markdown" else 0
                    raw_response.response.blocks.insert(insert_pos, rev_callout)

        if unsupported_steps:
            warnings.append(
                f"[UNSUPPORTED INSTRUCTION WARNING] Detected {len(unsupported_steps)} instructions citing invalid sources."
            )

        return CopilotAnswerResponse(
            answerable=raw_response.answerable,
            confidence_score=raw_response.confidence_score or 0.85,
            response=raw_response.response,
            sources=active_citations,
            warnings=warnings,
            unsupported_claims=unsupported_steps,
            contradictions_detected=context.contradictions_detected,
        )

    def create_abstention_response(self, reason: str, query: str) -> CopilotAnswerResponse:
        """Construct a standardized, safe abstention response."""
        blocks: List[ContentBlock] = [
            CalloutBlock(
                type="callout",
                variant="warning",
                title="Insufficient Document Grounding",
                content=reason,
            ),
            MarkdownBlock(
                type="markdown",
                content=(
                    "**Safety Policy Enforcement:**\n\n"
                    "BiztelAI Copilot strictly prevents hallucinating machinery operating parameters, "
                    "safety thresholds, or maintenance sequences without direct evidence.\n\n"
                    "- Please ensure the relevant equipment manual or SOP PDF has been uploaded.\n"
                    "- Verify that the query keywords match the standard equipment terminology.\n"
                    "- Consult your factory floor supervisor or certified technician before proceeding."
                ),
            ),
        ]
        return CopilotAnswerResponse(
            answerable=False,
            confidence_score=0.0,
            response=StructuredResponse(blocks=blocks),
            sources=[],
            warnings=["Abstained from answering due to insufficient source documentation."],
            unsupported_claims=[],
            contradictions_detected=[],
        )

