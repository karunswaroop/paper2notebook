"""Unit tests for PDF parser — page count limit (Task 1, Finding F10)."""
import fitz  # PyMuPDF
import pytest

from backend.services.pdf_parser import extract_text_from_pdf, MAX_PAGES


def _make_pdf(num_pages: int) -> bytes:
    """Create a minimal PDF with the given number of pages."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 72), f"Page {i + 1} content")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_max_pages_constant():
    assert MAX_PAGES == 200


def test_valid_pdf_under_limit():
    pdf_bytes = _make_pdf(5)
    result = extract_text_from_pdf(pdf_bytes)
    assert result["total_pages"] == 5
    assert "Page 1 content" in result["full_text"]
    assert len(result["pages"]) == 5


def test_pdf_at_exact_limit():
    pdf_bytes = _make_pdf(200)
    result = extract_text_from_pdf(pdf_bytes)
    assert result["total_pages"] == 200


def test_pdf_over_limit_raises():
    pdf_bytes = _make_pdf(201)
    with pytest.raises(ValueError, match="exceeds maximum"):
        extract_text_from_pdf(pdf_bytes)


def test_single_page_pdf():
    pdf_bytes = _make_pdf(1)
    result = extract_text_from_pdf(pdf_bytes)
    assert result["total_pages"] == 1
    assert len(result["pages"]) == 1
