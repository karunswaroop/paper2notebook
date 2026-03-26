"""Integration tests for security headers middleware (Task 8, Finding F8)."""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_has_security_headers():
    resp = client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in resp.headers["Permissions-Policy"]
    assert "microphone=()" in resp.headers["Permissions-Policy"]
    assert "geolocation=()" in resp.headers["Permissions-Policy"]
    assert resp.headers["Cache-Control"] == "no-store"


def test_generate_has_security_headers():
    """Even error responses should have security headers."""
    resp = client.post("/api/generate", data={"api_key": "test"})
    # Will be 422 or 400, but headers should still be present
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
