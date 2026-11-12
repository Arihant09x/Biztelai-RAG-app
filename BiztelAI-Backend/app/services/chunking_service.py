"""Structure-aware PDF chunking service for manufacturing SOPs and technical manuals."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.services.pdf_extraction_service import ExtractedPage, ExtractedTable
from app.utils.token_counter import estimate_tokens


@dataclass
class ProcessedChunk:
    chunk_index: int
    page_number: int
    section_heading: Optional[str]
    subheading: Optional[str]
    content: str
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_chunk_index: Optional[int] = None


class ChunkingService:
    """Splits extracted document pages into structure-preserving, context-rich chunks."""

    def __init__(self, target_chunk_tokens: int = 700, overlap_tokens: int = 100):
        self.target_chunk_tokens = target_chunk_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_document(
        self,
        pages: List[ExtractedPage],
        document_id: str,
        document_title: str,
        category: Optional[str] = None,
        department: Optional[str] = None,
    ) -> List[ProcessedChunk]:
        """Convert extracted pages into hierarchical, structure-aware chunks."""
        chunks: List[ProcessedChunk] = []
        chunk_idx = 0

        current_heading: Optional[str] = None
        current_subheading: Optional[str] = None

        for page in pages:
            page_text = page.text
            page_num = page.page_number

            # Also incorporate extracted tables into markdown representation
            table_markdown_blocks = self._format_tables_as_markdown(page.tables)

            # Detect headings if present on this page
            if page.headings:
                current_heading = page.headings[0]
                if len(page.headings) > 1:
                    current_subheading = page.headings[1]

            # Split text by structural boundaries (sections, numbered steps, safety warnings)
            logical_units = self._split_into_logical_units(page_text)

            # Append tables as distinct logical units
            for tbl_md in table_markdown_blocks:
                logical_units.append(tbl_md)

            # Group logical units into chunks respecting token budget (~700 tokens)
            current_chunk_text = ""
            current_tokens = 0
            unit_start_heading = current_heading
            unit_start_subheading = current_subheading

            for unit in logical_units:
                unit_tokens = estimate_tokens(unit)

                # Check if this unit itself defines a new section heading
                detected_h = self._detect_inline_heading(unit)
                if detected_h:
                    current_heading = detected_h

                if (current_tokens + unit_tokens) > self.target_chunk_tokens and current_chunk_text.strip():
                    # Finalize previous chunk
                    chunks.append(
                        ProcessedChunk(
                            chunk_index=chunk_idx,
                            page_number=page_num,
                            section_heading=unit_start_heading or document_title,
                            subheading=unit_start_subheading,
                            content=current_chunk_text.strip(),
                            token_count=current_tokens,
                            metadata={
                                "document_id": document_id,
                                "document_title": document_title,
                                "page_number": page_num,
                                "category": category,
                                "department": department,
                                "has_safety_warning": self._has_safety_alert(current_chunk_text),
                                "is_procedure": self._is_procedural_text(current_chunk_text),
                            },
                        )
                    )
                    chunk_idx += 1

                    # Apply overlap from end of previous chunk if possible
                    overlap_text = self._extract_overlap(current_chunk_text, self.overlap_tokens)
                    current_chunk_text = (overlap_text + "\n\n" + unit) if overlap_text else unit
                    current_tokens = estimate_tokens(current_chunk_text)
                    unit_start_heading = current_heading
                    unit_start_subheading = current_subheading
                else:
                    if current_chunk_text:
                        current_chunk_text += "\n\n" + unit
                    else:
                        current_chunk_text = unit
                    current_tokens += unit_tokens

            # Flush any remaining text for this page
            if current_chunk_text.strip():
                chunks.append(
                    ProcessedChunk(
                        chunk_index=chunk_idx,
                        page_number=page_num,
                        section_heading=unit_start_heading or document_title,
                        subheading=unit_start_subheading,
                        content=current_chunk_text.strip(),
                        token_count=current_tokens,
                        metadata={
                            "document_id": document_id,
                            "document_title": document_title,
                            "page_number": page_num,
                            "category": category,
                            "department": department,
                            "has_safety_warning": self._has_safety_alert(current_chunk_text),
                            "is_procedure": self._is_procedural_text(current_chunk_text),
                        },
                    )
                )
                chunk_idx += 1

        return chunks

    def _split_into_logical_units(self, text: str) -> List[str]:
        """Split text while keeping procedures, warnings, and lists intact."""
        if not text:
            return []

        # Split on double newlines
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        units: List[str] = []

        current_procedure_group: List[str] = []

        for p in paragraphs:
            # Check if this paragraph is part of a numbered list (e.g. "1. ", "Step 1:", "1) ")
            is_step = bool(re.match(r"^(\d+[\.\)]|Step\s+\d+:?|Phase\s+\d+:?|\*|\-)\s+", p, re.IGNORECASE))

            # Safety warnings must always be preserved as dedicated or grouped units
            is_warning = self._has_safety_alert(p)

            if is_step:
                current_procedure_group.append(p)
            else:
                if current_procedure_group:
                    # Flush accumulated procedure steps as one coherent logical unit
                    units.append("\n".join(current_procedure_group))
                    current_procedure_group = []

                if is_warning:
                    # Tag safety warning clearly
                    tagged_warning = f"[SAFETY WARNING]\n{p}" if not p.startswith("[SAFETY WARNING]") else p
                    units.append(tagged_warning)
                else:
                    units.append(p)

        if current_procedure_group:
            units.append("\n".join(current_procedure_group))

        return units

    def _format_tables_as_markdown(self, tables: List[ExtractedTable]) -> List[str]:
        """Convert extracted table data into structured Markdown table syntax."""
        markdown_tables = []
        for tbl in tables:
            if not tbl.headers or not tbl.rows:
                continue
            header_line = "| " + " | ".join(tbl.headers) + " |"
            sep_line = "| " + " | ".join(["---"] * len(tbl.headers)) + " |"
            row_lines = ["| " + " | ".join(row) + " |" for row in tbl.rows]
            table_md = "\n".join([header_line, sep_line] + row_lines)
            markdown_tables.append(f"[TABLE DATA (Page {tbl.page_number})]\n{table_md}")
        return markdown_tables

    def _extract_overlap(self, text: str, overlap_tokens: int) -> str:
        """Extract trailing sentences representing roughly overlap_tokens."""
        if not text or overlap_tokens <= 0:
            return ""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        collected: List[str] = []
        collected_tokens = 0
        for s in reversed(sentences):
            toks = estimate_tokens(s)
            if (collected_tokens + toks) > overlap_tokens:
                break
            collected.insert(0, s)
            collected_tokens += toks
        return " ".join(collected)

    def _detect_inline_heading(self, text: str) -> Optional[str]:
        """Identify if text looks like a heading or section title."""
        lines = text.strip().split("\n")
        first = lines[0].strip()
        if len(lines) == 1 and len(first) < 100:
            if re.match(r"^(SECTION|CHAPTER|\d+(\.\d+)*)\s+", first, re.IGNORECASE) or first.isupper():
                return first
        return None

    def _has_safety_alert(self, text: str) -> bool:
        """Check if text contains safety critical warning keywords."""
        pattern = r"\b(DANGER|WARNING|CAUTION|SAFETY\s+ALERT|PPE|LOCKOUT|TAGOUT|HAZARD)\b"
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _is_procedural_text(self, text: str) -> bool:
        """Check if text outlines procedural execution instructions."""
        pattern = r"(\bStep\s+\d+|\bPhase\s+\d+|^\d+[\.\)]\s+|\bInspect\b|\bVerify\b|\bTurn\s+off\b|\bConnect\b)"
        return bool(re.search(pattern, text, re.IGNORECASE | re.MULTILINE))

