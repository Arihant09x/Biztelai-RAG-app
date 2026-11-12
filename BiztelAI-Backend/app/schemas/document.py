"""Document metadata and detail response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadMetadata(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = Field(default="General", max_length=100)
    department: Optional[str] = Field(default=None, max_length=100)
    access_scope: Optional[str] = Field(default="public", description="public, internal, restricted")


class DocumentResponse(BaseModel):
    id: Union[str, UUID]
    title: str
    original_filename: str
    file_size_bytes: int
    sha256_hash: str
    category: Optional[str] = None
    department: Optional[str] = None
    access_scope: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentPageResponse(BaseModel):
    page_number: int
    raw_text: str
    has_ocr: bool
    page_metadata: Dict[str, Any] = Field(default_factory=dict)
    text_content: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if not self.text_content and self.raw_text:
            self.text_content = self.raw_text


class DocumentChunkResponse(BaseModel):
    id: Union[str, UUID]
    chunk_index: int
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    subheading: Optional[str] = None
    content: str
    token_count: int

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    total_pages: int = 0
    total_chunks: int = 0
    pages: List[DocumentPageResponse] = Field(default_factory=list)
