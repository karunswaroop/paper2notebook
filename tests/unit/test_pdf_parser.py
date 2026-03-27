"""Unit tests for PDF parser — page count limit and edge cases."""
import fitz  # PyMuPDF
import pytest

from backend.services.pdf_parser import extract_text_from_pdf, MAX_PAGES


def _make_pdf(num_pages: int, text_fn=None) -> bytes:
    """Create a minimal PDF with the given number of pages."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=612, height=792)
        text = text_fn(i) if text_fn else f"Page {i + 1} content"
        page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _make_blank_pdf(num_pages: int) -> bytes:
    """Create a PDF with blank pages (no text inserted)."""
    doc = fitz.open()
    for _ in range(num_pages):
        doc.new_page(width=612, height=792)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# --- Existing tests (v2) ---


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


# --- v3 edge case tests ---


def test_corrupted_bytes_raises():
    """Corrupted / non-PDF bytes should raise an exception."""
    with pytest.raises(Exception):
        extract_text_from_pdf(b"this is not a pdf at all")


def test_empty_bytes_raises():
    """Empty bytes should raise an exception."""
    with pytest.raises(Exception):
        extract_text_from_pdf(b"")


def test_blank_pdf_returns_empty_text():
    """A valid PDF with blank pages (no text) returns empty strings."""
    pdf_bytes = _make_blank_pdf(3)
    result = extract_text_from_pdf(pdf_bytes)
    assert result["total_pages"] == 3
    assert result["full_text"].strip() == ""
    for page in result["pages"]:
        assert page["text"].strip() == ""


def test_unicode_latin_text_preserved():
    """Latin-extended Unicode characters (accents) survive PDF extraction."""
    pdf_bytes = _make_pdf(1, text_fn=lambda _: "Résumé with àccénts and naïve café")
    result = extract_text_from_pdf(pdf_bytes)
    assert result["total_pages"] == 1
    assert "Résumé" in result["full_text"]
    assert "àccénts" in result["full_text"]
    assert "naïve" in result["full_text"]
    assert "café" in result["full_text"]


def test_page_numbers_sequential():
    """Each page dict has the correct 1-based page_number."""
    pdf_bytes = _make_pdf(5)
    result = extract_text_from_pdf(pdf_bytes)
    for i, page in enumerate(result["pages"]):
        assert page["page_number"] == i + 1


def test_full_text_joins_pages_with_double_newline():
    """full_text is pages joined by double newlines."""
    pdf_bytes = _make_pdf(3)
    result = extract_text_from_pdf(pdf_bytes)
    parts = [p["text"] for p in result["pages"]]
    assert result["full_text"] == "\n\n".join(parts)


def test_return_dict_has_required_keys():
    """Return value always has pages, full_text, and total_pages keys."""
    pdf_bytes = _make_pdf(1)
    result = extract_text_from_pdf(pdf_bytes)
    assert "pages" in result
    assert "full_text" in result
    assert "total_pages" in result


def test_over_limit_error_message_contains_page_count():
    """The ValueError message includes the actual page count."""
    pdf_bytes = _make_pdf(201)
    with pytest.raises(ValueError, match="201 pages"):
        extract_text_from_pdf(pdf_bytes)


def test_image_only_pdf_returns_empty_text():
    """A PDF with only a drawn rectangle (no text) returns empty strings."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    # Draw a filled rectangle instead of inserting text
    page.draw_rect(fitz.Rect(100, 100, 300, 300), color=(0, 0, 0), fill=(0.5, 0.5, 0.5))
    pdf_bytes = doc.tobytes()
    doc.close()

    result = extract_text_from_pdf(pdf_bytes)
    assert result["total_pages"] == 1
    assert result["full_text"].strip() == ""
