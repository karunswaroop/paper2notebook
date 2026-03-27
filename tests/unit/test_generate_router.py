"""Unit tests for the generate.py router — validation and error paths.

Tests use httpx AsyncClient with ASGITransport to exercise the router
in isolation, mocking all service-layer functions.
"""

import io
import logging
from unittest.mock import patch

import httpx
import nbformat
import pytest

from backend.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_EXTRACTED = {
    "pages": [{"page_number": 1, "text": "Sample paper text"}],
    "full_text": "Sample paper text for testing purposes",
    "total_pages": 1,
}

MOCK_CELLS = [
    {"cell_type": "markdown", "source": "# Tutorial"},
    {"cell_type": "code", "source": "print('hello')"},
]


def _mock_build_notebook(cells, title):
    """Return a minimal valid notebook node."""
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_markdown_cell(f"# {title}"))
    for c in cells:
        if c.get("cell_type") == "code":
            nb.cells.append(nbformat.v4.new_code_cell(c["source"]))
        else:
            nb.cells.append(nbformat.v4.new_markdown_cell(c.get("source", "")))
    return nb


def _service_mocks():
    """Return a stack of three patches for the service layer."""
    return (
        patch(
            "backend.routers.generate.extract_text_from_pdf",
            return_value=MOCK_EXTRACTED,
        ),
        patch(
            "backend.routers.generate.generate_notebook_content",
            return_value=MOCK_CELLS,
        ),
        patch(
            "backend.routers.generate.build_notebook",
            side_effect=_mock_build_notebook,
        ),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def _reset_limiters():
    """Reset rate-limiter storage so tests don't interfere with each other."""
    from backend.main import limiter as main_limiter
    from backend.routers.generate import limiter as router_limiter

    main_limiter.reset()
    router_limiter.reset()
    yield
    main_limiter.reset()
    router_limiter.reset()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_uppercase_pdf_extension_accepted(_reset_limiters):
    """Filename with uppercase .PDF extension should be accepted."""
    p1, p2, p3 = _service_mocks()
    with p1, p2, p3:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/api/generate",
                files={"file": ("paper.PDF", b"%PDF-1.4 fake content", "application/pdf")},
                data={"api_key": "sk-test-key"},
            )
    assert response.status_code == 200
    body = response.json()
    assert "notebook" in body


@pytest.mark.asyncio
async def test_no_extension_rejected_400(_reset_limiters):
    """Filename with no extension should be rejected with 400."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/generate",
            files={"file": ("paper_no_ext", b"some bytes", "application/pdf")},
            data={"api_key": "sk-test-key"},
        )
    assert response.status_code == 400
    assert "pdf" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_empty_filename_rejected_400(_reset_limiters):
    """Empty filename should be rejected with 400."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/generate",
            files={"file": ("", b"some bytes", "application/pdf")},
            data={"api_key": "sk-test-key"},
        )
    # FastAPI may reject the empty filename at the form-parsing level (422)
    # or the router rejects it (400). Both are acceptable.
    assert response.status_code in (400, 422)
    if response.status_code == 400:
        assert "pdf" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_whitespace_only_api_key_rejected_400(_reset_limiters):
    """Empty / whitespace-only API key should be rejected with 400."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/generate",
            files={"file": ("paper.pdf", b"%PDF-1.4 fake", "application/pdf")},
            data={"api_key": "   "},
        )
    assert response.status_code == 400
    assert "api key" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_empty_api_key_rejected_400(_reset_limiters):
    """Completely empty API key string should be rejected with 400."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/generate",
            files={"file": ("paper.pdf", b"%PDF-1.4 fake", "application/pdf")},
            data={"api_key": ""},
        )
    # FastAPI may return 422 (missing required field) or 400; both are acceptable
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_pdf_at_exact_50mb_limit_accepted(_reset_limiters):
    """PDF bytes exactly at the 50 MB boundary should be accepted."""
    max_size = 50 * 1024 * 1024  # 50 MB
    big_payload = b"%PDF-1.4 " + b"\x00" * (max_size - 9)  # exactly 50 MB

    p1, p2, p3 = _service_mocks()
    with p1, p2, p3:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/api/generate",
                files={"file": ("paper.pdf", big_payload, "application/pdf")},
                data={"api_key": "sk-test-key"},
            )
    assert response.status_code == 200
    body = response.json()
    assert "notebook" in body


@pytest.mark.asyncio
async def test_request_logging_contains_expected_fields(_reset_limiters, caplog):
    """Request log line should include client IP, filename, and size."""
    p1, p2, p3 = _service_mocks()
    with p1, p2, p3:
        with caplog.at_level(logging.INFO, logger="backend.routers.generate"):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
                await ac.post(
                    "/api/generate",
                    files={"file": ("research.pdf", b"%PDF-1.4 fake content", "application/pdf")},
                    data={"api_key": "sk-test-key"},
                )

    # Find the request-log line
    request_logs = [
        r.message for r in caplog.records
        if "POST /api/generate" in r.message and "filename=" in r.message
    ]
    assert len(request_logs) >= 1, f"Expected request log line, got: {[r.message for r in caplog.records]}"
    log_line = request_logs[0]
    assert "client=" in log_line
    assert "filename=research.pdf" in log_line
    assert "size=" in log_line


@pytest.mark.asyncio
async def test_success_response_logs_duration_and_cell_count(_reset_limiters, caplog):
    """Success log line should include duration and cell count."""
    p1, p2, p3 = _service_mocks()
    with p1, p2, p3:
        with caplog.at_level(logging.INFO, logger="backend.routers.generate"):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
                await ac.post(
                    "/api/generate",
                    files={"file": ("research.pdf", b"%PDF-1.4 fake content", "application/pdf")},
                    data={"api_key": "sk-test-key"},
                )

    # Find the success-log line
    success_logs = [
        r.message for r in caplog.records
        if "outcome=success" in r.message
    ]
    assert len(success_logs) >= 1, f"Expected success log line, got: {[r.message for r in caplog.records]}"
    log_line = success_logs[0]
    assert "duration=" in log_line
    assert "cells=" in log_line
