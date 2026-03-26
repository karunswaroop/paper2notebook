"""Integration tests for rate limiting (Task 6, Finding F4)."""
import io
import fitz
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_rate_limit():
    """Health endpoint should allow up to 60 req/min, then 429."""
    # Send 61 requests — the 61st should be rate limited
    for i in range(60):
        resp = client.get("/health")
        assert resp.status_code == 200, f"Request {i+1} failed unexpectedly"
    resp = client.get("/health")
    assert resp.status_code == 429


def test_generate_rate_limit():
    """Generate endpoint should allow up to 5 req/min, then 429."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Test content")
    pdf_bytes = doc.tobytes()
    doc.close()

    for i in range(5):
        resp = client.post(
            "/api/generate",
            files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            data={"api_key": "sk-test"},
        )
        # These will fail at LLM step (502/401) but should NOT be 429
        assert resp.status_code != 429, f"Request {i+1} was rate limited too early"

    # 6th request should be rate limited
    resp = client.post(
        "/api/generate",
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"api_key": "sk-test"},
    )
    assert resp.status_code == 429


def test_rate_limit_returns_json():
    """Rate limit response should be JSON, not HTML."""
    for _ in range(61):
        client.get("/health")
    resp = client.get("/health")
    assert resp.status_code == 429
    data = resp.json()
    assert "error" in data or "detail" in data
