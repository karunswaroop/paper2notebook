import json
import re
from openai import OpenAI

MAX_TEXT_LENGTH = 100_000

# Patterns that could be used for prompt injection
_INJECTION_PATTERNS = [
    # Delimiter faking
    r"---\s*(?:END\s+)?PAPER\s+TEXT\s*---",
    # Instruction overrides
    r"ignore\s+all\s+previous\s+instructions",
    r"you\s+are\s+now\s+",
    r"system\s*:",
    r"disregard\s+(?:all\s+)?(?:previous|above|prior)\s+",
    # Role injection tokens
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"<<SYS>>",
    r"<</SYS>>",
]


def sanitize_text(text: str) -> str:
    """Strip prompt-injection patterns and truncate to safe length."""
    for pattern in _INJECTION_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    return text[:MAX_TEXT_LENGTH]

SYSTEM_PROMPT = """You are an expert at converting research papers into educational Google Colab tutorial notebooks.

Given the text of a research paper, generate a structured tutorial notebook that:
1. Explains the key concepts, algorithms, and methodology from the paper
2. Implements the main algorithms in Python code cells
3. Includes visualizations and plots to illustrate results
4. Uses clear markdown explanations between code cells

Respond ONLY with a JSON object in this exact format:
{
  "cells": [
    {"cell_type": "markdown", "source": "markdown content here"},
    {"cell_type": "code", "source": "python code here"},
    ...
  ]
}

Guidelines:
- Start with a title and overview markdown cell
- Include a setup/install code cell early (pip installs for numpy, matplotlib, etc.)
- Alternate between explanation (markdown) and implementation (code) cells
- Include visualization code cells using matplotlib or seaborn
- Make code cells self-contained and runnable in Google Colab
- Add comments in code cells for clarity
- End with a summary/conclusion markdown cell
- Generate 10-20 cells total for a thorough tutorial"""


def build_prompt(paper_text: str) -> str:
    safe_text = sanitize_text(paper_text)
    return f"""Convert the following research paper into a tutorial notebook.
Focus on implementing the key algorithms, methodology, and include visualization/plot cells.
Generate code cells with working Python code and markdown cells with clear explanations.

--- PAPER TEXT ---
{safe_text}
--- END PAPER TEXT ---"""


def generate_notebook_content(paper_text: str, api_key: str) -> list[dict]:
    """Call GPT-4o to generate notebook cells from paper text."""
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(paper_text)},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    parsed = json.loads(content)
    return parsed.get("cells", [])
