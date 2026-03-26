"""Integration tests for error response sanitization (Task 5, Finding F6)."""
import io
import fitz
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _make_pdf(num_pages: int = 1) -> bytes:
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 72), f"Page {i + 1} content here")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_generic_error_on_llm_failure():
    """LLM errors should return generic message without exception details."""
    pdf_bytes = _make_pdf()
    with patch("backend.routers.generate.generate_notebook_content") as mock_llm:
        mock_llm.side_effect = RuntimeError("Connection to api.openai.com failed with key sk-abc123secret")
        response = client.post(
            "/api/generate",
            files={"file": ("paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            data={"api_key": "sk-test"},
        )
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "sk-abc123secret" not in detail
    assert "Connection to api.openai.com" not in detail
    assert detail == "LLM generation failed. Please try again."


def test_generic_error_on_unexpected_exception():
    """Unexpected exceptions should not leak internal details."""
    pdf_bytes = _make_pdf()
    with patch("backend.routers.generate.generate_notebook_content") as mock_llm:
        mock_llm.side_effect = Exception("Internal error at /Users/dev/secret/path.py line 42")
        response = client.post(
            "/api/generate",
            files={"file": ("paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            data={"api_key": "sk-test"},
        )
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "/Users/dev" not in detail
    assert "line 42" not in detail
    assert detail == "LLM generation failed. Please try again."


def test_auth_error_still_specific():
    """Auth errors should still return the specific auth message."""
    pdf_bytes = _make_pdf()
    with patch("backend.routers.generate.generate_notebook_content") as mock_llm:
        mock_llm.side_effect = RuntimeError("Invalid API key provided")
        response = client.post(
            "/api/generate",
            files={"file": ("paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            data={"api_key": "sk-bad"},
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key."
