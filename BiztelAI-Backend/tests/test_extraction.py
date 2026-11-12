"""Tests for PDF extraction, layout analysis, table detection, and text cleaning."""

import io
from pathlib import Path
import pymupdf
import pytest
from app.services.pdf_extraction_service import PDFExtractionService


def test_pdf_extraction_headings_and_pages(tmp_path):
    pdf_file = tmp_path / "test_sop.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    # Insert heading
    page.insert_text((50, 50), "SECTION 1: SAFETY RULES", fontsize=16)
    # Insert body
    page.insert_text((50, 90), "All operators must wear protective eyewear.\nLock out high voltage panels.", fontsize=10)
    doc.save(str(pdf_file))
    doc.close()

    extractor = PDFExtractionService(ocr_enabled=False)
    result = extractor.extract(pdf_file)

    assert result.total_pages == 1
    assert len(result.pages) == 1
    page_obj = result.pages[0]
    assert "protective eyewear" in page_obj.text
    assert "Lock out high voltage panels" in page_obj.text
    assert page_obj.page_number == 1


def test_repeated_header_footer_stripping():
    extractor = PDFExtractionService(ocr_enabled=False)
    from app.services.pdf_extraction_service import ExtractedPage

    # 4 pages with repeated header and footer
    pages = [
        ExtractedPage(page_number=i, text=f"COMPANY CONFIDENTIAL SOP\nActual content for page {i}\nPage {i} of 4")
        for i in range(1, 5)
    ]
    cleaned = extractor._strip_repeated_headers_and_footers(pages)
    for p in cleaned:
        assert "COMPANY CONFIDENTIAL SOP" not in p.text
        assert "Actual content for page" in p.text

