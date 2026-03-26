"""Integration tests for CORS configuration (Task 7, Finding F7)."""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

ORIGIN = "http://localhost:3000"


def test_cors_allows_localhost_3000():
    resp = client.options(
        "/api/generate",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert resp.headers.get("access-control-allow-origin") == ORIGIN


def test_cors_blocks_unknown_origin():
    resp = client.options(
        "/api/generate",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.headers.get("access-control-allow-origin") != "http://evil.com"


def test_cors_allows_post():
    resp = client.options(
        "/api/generate",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
        },
    )
    allowed = resp.headers.get("access-control-allow-methods", "")
    assert "POST" in allowed


def test_cors_does_not_allow_delete():
    resp = client.options(
        "/api/generate",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "DELETE",
        },
    )
    allowed = resp.headers.get("access-control-allow-methods", "")
    assert "DELETE" not in allowed
