import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.services.llm_service import generate_notebook_content, build_prompt


def test_build_prompt_includes_paper_text():
    paper_text = "This paper proposes a novel attention mechanism."
    prompt = build_prompt(paper_text)
    assert "attention mechanism" in prompt


def test_build_prompt_requests_code_and_explanations():
    prompt = build_prompt("Some paper text")
    assert "code" in prompt.lower()
    assert "markdown" in prompt.lower() or "explanation" in prompt.lower()
    assert "visualization" in prompt.lower() or "plot" in prompt.lower()


def test_generate_notebook_content_returns_cells():
    mock_response_content = json.dumps({
        "cells": [
            {"cell_type": "markdown", "source": "# Tutorial"},
            {"cell_type": "code", "source": "import numpy as np"},
            {"cell_type": "markdown", "source": "## Visualization"},
            {"cell_type": "code", "source": "import matplotlib.pyplot as plt\nplt.plot([1,2,3])"},
        ]
    })

    mock_message = MagicMock()
    mock_message.content = mock_response_content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("backend.services.llm_service.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        MockOpenAI.return_value = mock_client

        result = generate_notebook_content("Paper about neural nets", "sk-fake")

    assert isinstance(result, list)
    assert len(result) == 4
    assert result[0]["cell_type"] == "markdown"
    assert result[1]["cell_type"] == "code"


def test_generate_notebook_content_calls_openai_with_correct_model():
    mock_message = MagicMock()
    mock_message.content = json.dumps({"cells": []})
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("backend.services.llm_service.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        MockOpenAI.return_value = mock_client

        generate_notebook_content("Paper text", "sk-fake")

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4o"
