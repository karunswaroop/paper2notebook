import sys
import os
import io
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import fitz
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def _make_real_pdf():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Attention Is All You Need\n\nAbstract\nThis paper proposes a new architecture.", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_full_pipeline_with_mocked_llm():
    mock_cells = json.dumps({
        "cells": [
            {"cell_type": "markdown", "source": "# Tutorial on Attention"},
            {"cell_type": "code", "source": "import numpy as np"},
        ]
    })
    mock_message = MagicMock()
    mock_message.content = mock_cells
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("backend.services.llm_service.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        MockOpenAI.return_value = mock_client

        pdf = _make_real_pdf()
        response = client.post(
            "/api/generate",
            data={"api_key": "sk-test"},
            files={"file": ("paper.pdf", io.BytesIO(pdf), "application/pdf")},
        )

    assert response.status_code == 200
    body = response.json()
    nb = body["notebook"]
    assert nb["nbformat"] == 4
    # Should have title + setup + 2 LLM cells = 4
    assert len(nb["cells"]) >= 4
    # First cell should be title
    assert "Tutorial Notebook" in nb["cells"][0]["source"]
    # Second cell should be setup
    assert "pip install" in nb["cells"][1]["source"]
