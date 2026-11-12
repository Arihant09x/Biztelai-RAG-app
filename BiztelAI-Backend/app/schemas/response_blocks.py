"""Strict Pydantic v2 schemas for rich structured response blocks.

Prevents arbitrary HTML/JS and strictly models the presentation blocks:
markdown, steps, checklist, callout, table, mermaid, image, source, quote,
comparison, accordion, progress.
"""

from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictBase(BaseModel):
    """Base schema rejecting extraneous properties."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# 1. Markdown Block
class MarkdownBlock(StrictBase):
    type: Literal["markdown"] = "markdown"
    content: str


# 2. Steps Block
class StepItem(StrictBase):
    id: str = Field(description="Step identifier e.g. step_1")
    content: str = Field(description="Instruction text grounded in source documentation")
    source_ids: List[str] = Field(default_factory=list, description="Referenced citation IDs")


class StepsBlock(StrictBase):
    type: Literal["steps"] = "steps"
    title: Optional[str] = "Procedure"
    items: List[StepItem]


# 3. Checklist Block
class ChecklistItem(StrictBase):
    id: str = Field(description="Checklist item identifier e.g. check_1")
    content: str = Field(description="Verification condition to be inspected")
    source_ids: List[str] = Field(default_factory=list, description="Referenced citation IDs")
    checked: bool = False


class ChecklistBlock(StrictBase):
    type: Literal["checklist"] = "checklist"
    title: Optional[str] = "Verification Checklist"
    items: List[ChecklistItem]


# 4. Callout Block
class CalloutBlock(StrictBase):
    type: Literal["callout"] = "callout"
    variant: Literal["info", "warning", "danger", "success", "note"] = "info"
    title: Optional[str] = None
    content: str
    source_ids: List[str] = Field(default_factory=list)


# 5. Table Block
class TableBlock(StrictBase):
    type: Literal["table"] = "table"
    title: Optional[str] = None
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None


# 6. Mermaid Block
class MermaidBlock(StrictBase):
    type: Literal["mermaid"] = "mermaid"
    title: Optional[str] = None
    chart: str

    @field_validator("chart")
    @classmethod
    def validate_chart_content(cls, v: str) -> str:
        v_stripped = v.strip()
        allowed_prefixes = ("graph ", "flowchart ", "sequenceDiagram", "stateDiagram", "classDiagram", "erDiagram")
        if not any(v_stripped.startswith(p) for p in allowed_prefixes):
            raise ValueError("Mermaid chart must start with a valid diagram type (e.g. flowchart TD, graph TD, sequenceDiagram)")
        return v_stripped


# 7. Image / Figure Block
class ImageBlock(StrictBase):
    type: Literal["image"] = "image"
    url: str
    alt: str
    caption: Optional[str] = None
    page_number: Optional[int] = None


# 8. Source Citation Schema & Block
class SourceCitation(StrictBase):
    id: str = Field(description="Unique citation handle e.g. source_1")
    document_id: str
    document_title: str
    page_number: Optional[int] = None
    snippet: str
    relevance_score: Optional[float] = None
    section: Optional[str] = None


class SourceBlock(StrictBase):
    type: Literal["source"] = "source"
    sources: List[SourceCitation]


# 9. Quote Block
class QuoteBlock(StrictBase):
    type: Literal["quote"] = "quote"
    quote: str
    author_or_source: Optional[str] = None
    page_number: Optional[int] = None
    source_id: Optional[str] = None


# 10. Comparison Block
class ComparisonItem(StrictBase):
    feature: str
    option_a: str
    option_b: str


class ComparisonBlock(StrictBase):
    type: Literal["comparison"] = "comparison"
    title: Optional[str] = "Comparison"
    headers: List[str] = Field(default_factory=lambda: ["Feature", "Option A", "Option B"])
    items: List[ComparisonItem]


# 11. Accordion Block
class AccordionSection(StrictBase):
    title: str
    content: str


class AccordionBlock(StrictBase):
    type: Literal["accordion"] = "accordion"
    sections: List[AccordionSection]


# 12. Progress Block
class ProgressBlock(StrictBase):
    type: Literal["progress"] = "progress"
    current: int
    total: int
    label: str


# Discriminated Union of all permitted UI blocks
ContentBlock = Annotated[
    Union[
        MarkdownBlock,
        StepsBlock,
        ChecklistBlock,
        CalloutBlock,
        TableBlock,
        MermaidBlock,
        ImageBlock,
        SourceBlock,
        QuoteBlock,
        ComparisonBlock,
        AccordionBlock,
        ProgressBlock,
    ],
    Field(discriminator="type"),
]


class StructuredResponse(StrictBase):
    """Container holding ordered sequence of structured UI blocks."""
    blocks: List[ContentBlock]


class CopilotAnswerResponse(StrictBase):
    """Top-level grounded answer envelope."""
    answerable: bool
    confidence_score: Optional[float] = None
    response: StructuredResponse
    sources: List[SourceCitation] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    contradictions_detected: List[str] = Field(default_factory=list)

