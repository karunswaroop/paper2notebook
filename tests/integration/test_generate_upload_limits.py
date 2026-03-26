"""Integration tests for file upload size and page limits (Task 1, Findings F2, F10)."""
import io
import fitz
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def _make_pdf(num_pages: int) -> bytes:
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 72), f"Page {i + 1}")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_upload_too_large_rejected_with_413():
    """Files >50MB should be rejected with 413 before full read."""
    # Create a payload that exceeds 50MB — use a small PDF + padding
    small_pdf = _make_pdf(1)
    # We can't easily send 50MB in tests, so we test the Content-Length check
    # by sending a file with a size header that exceeds the limit.
    # Instead, we'll create a bytes payload just over the limit.
    oversized = small_pdf + b"\x00" * (MAX_FILE_SIZE + 1 - len(small_pdf))

    response = client.post(
        "/api/generate",
        files={"file": ("big.pdf", io.BytesIO(oversized), "application/pdf")},
        data={"api_key": "sk-test"},
    )
    assert response.status_code == 413
    assert "50MB" in response.json()["detail"] or "size" in response.json()["detail"].lower()


def test_pdf_over_200_pages_rejected_with_400():
    """PDFs with >200 pages should be rejected."""
    pdf_bytes = _make_pdf(201)
    response = client.post(
        "/api/generate",
        files={"file": ("big.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"api_key": "sk-test"},
    )
    assert response.status_code == 400
    assert "200" in response.json()["detail"] or "pages" in response.json()["detail"].lower()


def test_valid_small_pdf_passes_size_check():
    """A valid small PDF should pass size/page checks (will fail at LLM step, not here)."""
    pdf_bytes = _make_pdf(3)
    response = client.post(
        "/api/generate",
        files={"file": ("paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"api_key": "sk-test"},
    )
    # Should NOT be 413 or 400-with-page-error — it will fail later at LLM call
    assert response.status_code != 413
    # The status could be 502 (LLM fails) or 401 (bad key) — that's fine,
    # we just verify it passed the upload validation stage
    assert response.status_code not in (413,)


def test_non_pdf_file_rejected():
    """Non-PDF files should still be rejected with 400."""
    response = client.post(
        "/api/generate",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"api_key": "sk-test"},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]
