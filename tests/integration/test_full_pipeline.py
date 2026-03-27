"""Integration tests for full POST /api/generate pipeline with mocked OpenAI."""
import io
import json
from unittest.mock import patch, MagicMock

import fitz
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def _make_real_pdf(text="Attention Is All You Need\n\nAbstract\nThis paper proposes a new architecture."):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _mock_openai_response(cells):
    """Create a mock OpenAI completion returning the given cells."""
    mock_message = MagicMock()
    mock_message.content = json.dumps({"cells": cells})
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    return mock_completion


def _post_generate(pdf_bytes, api_key="sk-test"):
    return client.post(
        "/api/generate",
        data={"api_key": api_key},
        files={"file": ("paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )


def test_valid_pdf_returns_200_with_notebook():
    """Full pipeline: valid PDF → 200 with notebook containing title + setup + LLM cells."""
    cells = [
        {"cell_type": "markdown", "source": "# Tutorial"},
        {"cell_type": "code", "source": "import numpy as np"},
    ]
    with patch("backend.services.llm_service.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value = _mock_openai_response(cells)
        response = _post_generate(_make_real_pdf())

    assert response.status_code == 200
    nb = response.json()["notebook"]
    assert nb["nbformat"] == 4
    # title + setup + 2 LLM cells = 4
    assert len(nb["cells"]) >= 4
    assert "Tutorial Notebook" in nb["cells"][0]["source"]
    assert "pip install" in nb["cells"][1]["source"]


def test_response_has_correct_nbformat():
    """Notebook in response has nbformat version 4."""
    cells = [{"cell_type": "markdown", "source": "# Test"}]
    with patch("backend.services.llm_service.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value = _mock_openai_response(cells)
        response = _post_generate(_make_real_pdf())

    nb = response.json()["notebook"]
    assert nb["nbformat"] == 4
    assert nb["nbformat_minor"] >= 0


def test_dangerous_code_gets_warning_comment():
    """LLM cells with dangerous patterns get warning prepended."""
    cells = [
        {"cell_type": "code", "source": "import os\nos.system('rm -rf /')"},
    ]
    with patch("backend.services.llm_service.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value = _mock_openai_response(cells)
        response = _post_generate(_make_real_pdf())

    assert response.status_code == 200
    nb = response.json()["notebook"]
    # Find the LLM code cell (after title + setup)
    llm_code_cell = nb["cells"][2]  # title=0, setup=1, first LLM=2
    assert "WARNING" in llm_code_cell["source"]


def test_empty_cells_produces_title_and_setup_only():
    """LLM returning empty cells array → notebook has only title + setup."""
    cells = []
    with patch("backend.services.llm_service.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value = _mock_openai_response(cells)
        response = _post_generate(_make_real_pdf())

    assert response.status_code == 200
    nb = response.json()["notebook"]
    assert len(nb["cells"]) == 2  # title + setup only


def test_openai_auth_error_returns_401():
    """OpenAI authentication error → 401 with 'Invalid API key'."""
    with patch("backend.services.llm_service.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = Exception(
            "Incorrect API key provided: sk-test. You can find your API key at https://platform.openai.com/account/api-keys."
        )
        response = _post_generate(_make_real_pdf())

    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


def test_openai_timeout_returns_502():
    """OpenAI timeout → 502 with generic message."""
    with patch("backend.services.llm_service.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = Exception(
            "Request timed out."
        )
        response = _post_generate(_make_real_pdf())

    assert response.status_code == 502
    assert "LLM generation failed" in response.json()["detail"]


def test_openai_rate_limit_returns_502():
    """OpenAI rate limit (429) → 502 with generic message."""
    with patch("backend.services.llm_service.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = Exception(
            "Rate limit reached for gpt-4o. Please retry after 20s."
        )
        response = _post_generate(_make_real_pdf())

    assert response.status_code == 502
    assert "LLM generation failed" in response.json()["detail"]
