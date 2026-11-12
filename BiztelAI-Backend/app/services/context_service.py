"""Context engineering service: token budgeting, citation mapping, and contradiction detection."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from app.schemas.response_blocks import SourceCitation
from app.services.retrieval_service import RetrievedChunk
from app.utils.token_counter import estimate_tokens, truncate_to_token_limit
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class EngineeredContext:
    context_text: str
    citations: List[SourceCitation]
    citation_map: Dict[str, RetrievedChunk]  # e.g. "source_1" -> chunk
    total_tokens: int
    contradictions_detected: List[str] = field(default_factory=list)
    has_safety_warnings: bool = False


class ContextEngineeringService:
    """Assembles and formats grounded evidence within LLM token budget limits."""

    def __init__(self, max_context_tokens: int = 3500):
        self.max_context_tokens = max_context_tokens

    @staticmethod
    def _extract_revision_metadata(text_str: str) -> Tuple[Optional[str], Optional[int], bool]:
        """Extract SOP document family code, revision number, and whether it supersedes an earlier revision."""
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

    def engineer_context(
        self,
        chunks: List[RetrievedChunk],
        query: str,
    ) -> EngineeredContext:
        """Filter, format, map citations, and detect contradictions/supersessions in retrieved chunks."""
        if not chunks:
            return EngineeredContext(
                context_text="No document evidence available.",
                citations=[],
                citation_map={},
                total_tokens=0,
            )

        citations: List[SourceCitation] = []
        citation_map: Dict[str, RetrievedChunk] = {}
        formatted_evidence_blocks: List[str] = []
        accumulated_tokens = 0
        has_safety = False

        # Identify highest revision per document family
        family_max_rev: Dict[str, int] = {}
        for chunk in chunks:
            fam, rev, _ = self._extract_revision_metadata(f"{chunk.document_title} {chunk.content}")
            if fam and rev is not None:
                family_max_rev[fam] = max(family_max_rev.get(fam, 0), rev)

        # Re-sort chunks so active latest revisions are prioritized within token budget
        def chunk_sort_key(c: RetrievedChunk):
            fam, rev, supersedes = self._extract_revision_metadata(f"{c.document_title} {c.content}")
            is_active = (fam in family_max_rev and rev == family_max_rev[fam]) if (fam and rev is not None) else True
            # active revisions first (0), obsolete revisions last (1)
            return (0 if is_active else 1, -(c.similarity_score or 0.0), -(c.rrf_score or 0.0))

        sorted_chunks = sorted(chunks, key=chunk_sort_key)

        # Detect contradictions and obsolete revision conflicts
        contradictions = self._detect_contradictions(sorted_chunks, family_max_rev)

        for idx, chunk in enumerate(sorted_chunks, start=1):
            source_id = f"source_{idx}"

            # Sanitize untrusted document content to prevent prompt injection
            safe_content = self._sanitize_untrusted_text(chunk.content)

            # Check if this chunk contains safety warnings
            if "[SAFETY WARNING]" in safe_content or any(w in safe_content.upper() for w in ["DANGER", "WARNING", "PPE"]):
                has_safety = True

            fam, rev, supersedes = self._extract_revision_metadata(f"{chunk.document_title} {chunk.content}")
            rev_status = "CURRENT"
            if fam and rev is not None and fam in family_max_rev:
                if rev < family_max_rev[fam]:
                    rev_status = f"OBSOLETE / SUPERSEDED (Superseded by Rev {family_max_rev[fam]:02d} - ISO 9001 ALERT: DO NOT USE FOR ACTIVE PROCEDURES)"
                else:
                    rev_status = f"ACTIVE APPROVED REVISION {rev:02d} (Current Shop-Floor Standard)"
            elif supersedes:
                rev_status = "ACTIVE APPROVED (Contains Supersession Authority)"

            # Format citation block
            citation_item = SourceCitation(
                id=source_id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                page_number=chunk.page_number,
                snippet=safe_content[:450] + ("..." if len(safe_content) > 450 else ""),
                relevance_score=round(chunk.similarity_score, 4) if chunk.similarity_score else None,
                section=chunk.section_heading,
            )

            chunk_header = (
                f"--- BEGIN EVIDENCE [{source_id}] ---\n"
                f"DOCUMENT: {chunk.document_title} (ID: {chunk.document_id})\n"
                f"REVISION STATUS: {rev_status}\n"
                f"PAGE: {chunk.page_number}\n"
                f"SECTION: {chunk.section_heading or 'General'}\n"
            )
            chunk_body = f"{chunk_header}\nCONTENT:\n{safe_content}\n--- END EVIDENCE [{source_id}] ---\n"
            chunk_tokens = estimate_tokens(chunk_body)

            if (accumulated_tokens + chunk_tokens) > self.max_context_tokens:
                # If budget exhausted, stop adding further chunks
                break

            citations.append(citation_item)
            citation_map[source_id] = chunk
            formatted_evidence_blocks.append(chunk_body)
            accumulated_tokens += chunk_tokens

        full_context_text = "\n\n".join(formatted_evidence_blocks)

        return EngineeredContext(
            context_text=full_context_text,
            citations=citations,
            citation_map=citation_map,
            total_tokens=accumulated_tokens,
            contradictions_detected=contradictions,
            has_safety_warnings=has_safety,
        )

    def _sanitize_untrusted_text(self, text: str) -> str:
        """Neutralize malicious injection instructions inside uploaded SOP documents."""
        if not text:
            return ""
        # Strip system prompt overrides or jailbreak patterns
        sanitized = re.sub(
            r"(?i)\b(ignore (all )?previous instructions|system prompt|you are now|disregard safety guidelines)\b",
            "[SECURITY FILTERED ATTEMPT]",
            text,
        )
        return sanitized.strip()

    def _detect_contradictions(
        self,
        chunks: List[RetrievedChunk],
        family_max_rev: Optional[Dict[str, int]] = None,
    ) -> List[str]:
        """Detect conflicting safety procedures, obsolete revisions, or contrasting operational values across documents."""
        contradictions: List[str] = []
        docs_involved = {c.document_title for c in chunks}

        # 1. ISO 9001 Document Revision Supersession Detection
        if family_max_rev:
            for fam, max_rev in family_max_rev.items():
                found_revs = set()
                for c in chunks:
                    c_fam, c_rev, _ = self._extract_revision_metadata(f"{c.document_title} {c.content}")
                    if c_fam == fam and c_rev is not None:
                        found_revs.add(c_rev)
                if len(found_revs) > 1:
                    for older_rev in found_revs:
                        if older_rev < max_rev:
                            contradictions.append(
                                f"ISO 9001 SUPERSEDED REVISION DETECTED: '{fam} Rev {older_rev:02d}' has been superseded by '{fam} Rev {max_rev:02d}'. "
                                f"In accordance with ISO 9001 Clause 7.5.3 (Control of Documented Information), shop-floor operations must strictly follow Rev {max_rev:02d}."
                            )

        # 2. Check if multiple differing documents discuss the same procedure with contrasting rules
        if len(docs_involved) > 1:
            # Check for conflicting PPE or torque/temperature specifications
            lockout_mentions = [c for c in chunks if "lockout" in c.content.lower()]
            tagout_mentions = [c for c in chunks if "tagout" in c.content.lower()]
            if lockout_mentions and not tagout_mentions and len(docs_involved) > 1:
                # Potential procedure divergence
                pass

            # Search for contradictory numerical values for same parameter (e.g., 50 PSI vs 100 PSI, 120 C vs 180 C)
            temp_matches = {}
            for c in chunks:
                matches = re.findall(r"(\d+)\s*(?:°C|deg\s*C|PSI|bar|RPM|Nm)", c.content, re.IGNORECASE)
                if matches:
                    temp_matches[c.document_title] = set(matches)

            if len(temp_matches) > 1:
                keys = list(temp_matches.keys())
                for i in range(len(keys)):
                    for j in range(i + 1, len(keys)):
                        diff = temp_matches[keys[i]].symmetric_difference(temp_matches[keys[j]])
                        if diff:
                            contradictions.append(
                                f"Potential operating specification divergence between '{keys[i]}' and '{keys[j]}' regarding: {', '.join(list(diff)[:3])}"
                            )

        return contradictions
