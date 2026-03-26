"""Integration tests for structured request logging (Task 12, Finding F9)."""
import io
import logging
import fitz
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _make_pdf(num_pages: int = 1) -> bytes:
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 72), f"Page {i + 1}")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_generate_logs_request_info(caplog):
    """Generate endpoint should log client info, filename, file size."""
    pdf_bytes = _make_pdf()
    with caplog.at_level(logging.INFO, logger="backend.routers.generate"):
        with patch("backend.routers.generate.generate_notebook_content") as mock_llm:
            mock_llm.side_effect = RuntimeError("test error")
            client.post(
                "/api/generate",
                files={"file": ("paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                data={"api_key": "sk-test123"},
            )
    log_text = caplog.text
    assert "paper.pdf" in log_text
    # API key should NEVER appear in logs
    assert "sk-test123" not in log_text


def test_api_key_never_logged(caplog):
    """API key must never appear in any log output."""
    pdf_bytes = _make_pdf()
    secret_key = "sk-super-secret-key-12345"
    with caplog.at_level(logging.DEBUG):
        with patch("backend.routers.generate.generate_notebook_content") as mock_llm:
            mock_llm.side_effect = RuntimeError("auth error with api key")
            client.post(
                "/api/generate",
                files={"file": ("paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                data={"api_key": secret_key},
            )
    assert secret_key not in caplog.text
