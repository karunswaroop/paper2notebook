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


def _make_pdf_bytes():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Sample research paper content", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_generate_returns_400_when_no_file():
    response = client.post(
        "/api/generate",
        data={"api_key": "sk-test"},
    )
    assert response.status_code == 422 or response.status_code == 400


def test_generate_returns_400_when_no_api_key():
    pdf = _make_pdf_bytes()
    response = client.post(
        "/api/generate",
        files={"file": ("test.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert response.status_code == 422 or response.status_code == 400


def test_generate_returns_400_for_non_pdf():
    response = client.post(
        "/api/generate",
        data={"api_key": "sk-test"},
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400
    assert "pdf" in response.json()["detail"].lower()


def test_generate_returns_200_with_valid_inputs():
    mock_cells = json.dumps({
        "cells": [
            {"cell_type": "markdown", "source": "# Tutorial"},
            {"cell_type": "code", "source": "print('hello')"},
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

        pdf = _make_pdf_bytes()
        response = client.post(
            "/api/generate",
            data={"api_key": "sk-test"},
            files={"file": ("paper.pdf", io.BytesIO(pdf), "application/pdf")},
        )

    assert response.status_code == 200
    body = response.json()
    assert "notebook" in body
    assert body["notebook"]["nbformat"] == 4
