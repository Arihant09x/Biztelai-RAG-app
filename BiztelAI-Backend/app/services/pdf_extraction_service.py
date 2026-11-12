"""PDF text, table, layout, and heading extraction service using PyMuPDF and OCR fallback."""

import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pymupdf  # fitz
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ExtractedTable:
    page_number: int
    headers: List[str]
    rows: List[List[str]]
    title: Optional[str] = None


@dataclass
class ExtractedImage:
    page_number: int
    image_index: int
    width: int
    height: int
    image_bytes: bytes
    caption: Optional[str] = None


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    has_ocr: bool = False
    headings: List[str] = field(default_factory=list)
    tables: List[ExtractedTable] = field(default_factory=list)
    images: List[ExtractedImage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    document_title: str
    total_pages: int
    pages: List[ExtractedPage]
    metadata: Dict[str, Any]

    @property
    def tables(self) -> List[ExtractedTable]:
        """Aggregate all extracted tables across all pages."""
        return [t for p in self.pages for t in getattr(p, "tables", [])]

    @property
    def images(self) -> List[ExtractedImage]:
        """Aggregate all extracted images across all pages."""
        return [img for p in self.pages for img in getattr(p, "images", [])]


class PDFExtractionService:
    """Extracts text, structural headings, tables, and images from PDF documents."""

    def __init__(self, ocr_enabled: bool = True):
        self.ocr_enabled = ocr_enabled

    def extract(self, file_path: Path) -> ExtractionResult:
        """Process PDF file page-by-page and extract text, layout, tables, and images."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        doc = pymupdf.open(str(file_path))
        doc_metadata = doc.metadata or {}
        document_title = doc_metadata.get("title") or file_path.stem
        total_pages = len(doc)

        raw_pages: List[ExtractedPage] = []

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]

            # 1. Extract text and identify headings using block font sizes
            text, headings = self._extract_text_and_headings(page)

            # 2. Check for missing or insufficient text; run OCR fallback if enabled
            has_ocr = False
            if len(text.strip()) < 50 and self.ocr_enabled:
                ocr_text = self._attempt_ocr(page)
                if ocr_text:
                    text = ocr_text
                    has_ocr = True

            # 3. Extract tables using PyMuPDF table finder
            tables = self._extract_tables(page, page_num)

            # 4. Extract embedded images
            images = self._extract_images(doc, page, page_num)

            raw_pages.append(
                ExtractedPage(
                    page_number=page_num,
                    text=text,
                    has_ocr=has_ocr,
                    headings=headings,
                    tables=tables,
                    images=images,
                    metadata={"char_count": len(text), "heading_count": len(headings)},
                )
            )

        # 5. Detect and remove repeated headers and footers across pages
        cleaned_pages = self._strip_repeated_headers_and_footers(raw_pages)

        doc.close()

        return ExtractionResult(
            document_title=document_title,
            total_pages=total_pages,
            pages=cleaned_pages,
            metadata=doc_metadata,
        )

    def _extract_text_and_headings(self, page: pymupdf.Page) -> Tuple[str, List[str]]:
        """Extract structured text and detect headings based on font size and formatting."""
        headings: List[str] = []
        text_lines: List[str] = []

        try:
            # Extract detailed block dictionary
            text_dict = page.get_text("dict", flags=pymupdf.TEXTFLAGS_SEARCH)
            blocks = text_dict.get("blocks", [])

            # Compute median font size on the page to identify headings
            font_sizes = []
            for b in blocks:
                if b.get("type") == 0:  # Text block
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            if span.get("size"):
                                font_sizes.append(span["size"])

            base_font_size = 10.0
            if font_sizes:
                sorted_sizes = sorted(font_sizes)
                base_font_size = sorted_sizes[len(sorted_sizes) // 2]

            for b in blocks:
                if b.get("type") == 0:  # Text block
                    block_text = ""
                    for line in b.get("lines", []):
                        line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                        # Check if line is styled as a heading (font size > base * 1.2 or bold)
                        is_heading = False
                        for span in line.get("spans", []):
                            size = span.get("size", base_font_size)
                            flags = span.get("flags", 0)
                            is_bold = bool(flags & 2)  # Bold flag in PyMuPDF
                            if size >= (base_font_size * 1.2) or (is_bold and len(line_text.strip()) < 80):
                                is_heading = True
                                break

                        clean_line = line_text.strip()
                        if clean_line:
                            if is_heading and len(clean_line) > 3 and not clean_line.isdigit():
                                headings.append(clean_line)
                            block_text += line_text + "\n"

                    if block_text.strip():
                        text_lines.append(block_text.strip())

            full_text = "\n\n".join(text_lines)
            if not full_text.strip():
                # Fallback to plain text
                full_text = page.get_text("text")

        except Exception as e:
            logger.warning("heading_extraction_fallback", error=str(e))
            full_text = page.get_text("text")

        return self._normalize_text(full_text), headings

    def _extract_tables(self, page: pymupdf.Page, page_number: int) -> List[ExtractedTable]:
        """Extract tabular structures using PyMuPDF table finder."""
        tables: List[ExtractedTable] = []
        try:
            tab_finder = page.find_tables()
            for tab in tab_finder.tables:
                extracted_data = tab.extract()
                if not extracted_data or len(extracted_data) < 2:
                    continue
                headers = [str(col or "").strip() for col in extracted_data[0]]
                rows = [[str(cell or "").strip() for cell in row] for row in extracted_data[1:]]
                tables.append(ExtractedTable(page_number=page_number, headers=headers, rows=rows))
        except Exception as e:
            logger.debug("table_extraction_skipped", page=page_number, error=str(e))
        return tables

    def _extract_images(self, doc: pymupdf.Document, page: pymupdf.Page, page_number: int) -> List[ExtractedImage]:
        """Extract embedded figures and images from PDF page."""
        images: List[ExtractedImage] = []
        try:
            image_list = page.get_images(full=True)
            for idx, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                if base_image and base_image.get("image"):
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)
                    # Skip tiny decorative icons/bullets
                    if width >= 100 and height >= 100:
                        images.append(
                            ExtractedImage(
                                page_number=page_number,
                                image_index=idx,
                                width=width,
                                height=height,
                                image_bytes=base_image["image"],
                            )
                        )
        except Exception as e:
            logger.debug("image_extraction_skipped", page=page_number, error=str(e))
        return images

    def _attempt_ocr(self, page: pymupdf.Page) -> Optional[str]:
        """Fallback OCR on scanned PDF pages using pytesseract or PyMuPDF pixmap."""
        try:
            import pytesseract
            from PIL import Image

            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text = pytesseract.image_to_string(img)
            return self._normalize_text(ocr_text)
        except Exception as e:
            logger.warning("ocr_fallback_unavailable", error=str(e))
            return None

    def _normalize_text(self, text: str) -> str:
        """Clean and normalize extracted text without destroying structure or numbers."""
        if not text:
            return ""
        # Replace non-breaking spaces
        text = text.replace("\xa0", " ").replace("\r\n", "\n")
        # Collapse excessive newlines (max 2)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Collapse multiple inline spaces
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _strip_repeated_headers_and_footers(self, pages: List[ExtractedPage]) -> List[ExtractedPage]:
        """Detect and remove repetitive headers/footers appearing across multiple pages."""
        if len(pages) < 3:
            return pages

        # Extract first line (potential header) and last line (potential footer) of each page
        first_lines: Dict[str, int] = {}
        last_lines: Dict[str, int] = {}

        for p in pages:
            lines = [l.strip() for l in p.text.split("\n") if l.strip()]
            if lines:
                first = lines[0]
                first_lines[first] = first_lines.get(first, 0) + 1
                last = lines[-1]
                last_lines[last] = last_lines.get(last, 0) + 1

        threshold = len(pages) * 0.6
        common_headers = {l for l, count in first_lines.items() if count >= threshold and len(l) > 3}
        common_footers = {l for l, count in last_lines.items() if count >= threshold and len(l) > 3}

        for p in pages:
            lines = p.text.split("\n")
            cleaned = []
            for idx, line in enumerate(lines):
                s = line.strip()
                if idx == 0 and s in common_headers:
                    continue
                if idx >= len(lines) - 2 and s in common_footers:
                    continue
                cleaned.append(line)
            p.text = "\n".join(cleaned).strip()

        return pages

