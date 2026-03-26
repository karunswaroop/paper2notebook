"""Unit test for LLM client timeout (Task 9, Finding F12)."""
from unittest.mock import patch, MagicMock

from backend.services.llm_service import generate_notebook_content


def test_openai_client_constructed_with_timeout():
    """The OpenAI client should be created with timeout=120.0."""
    with patch("backend.services.llm_service.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"cells": []}'
        mock_client.chat.completions.create.return_value = mock_response
        MockOpenAI.return_value = mock_client

        generate_notebook_content("test paper", "sk-test")

        MockOpenAI.assert_called_once_with(api_key="sk-test", timeout=120.0)
