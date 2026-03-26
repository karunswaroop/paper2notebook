import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import nbformat
from backend.services.notebook_builder import build_notebook


def _sample_cells():
    return [
        {"cell_type": "markdown", "source": "# Tutorial\nOverview of the paper."},
        {"cell_type": "code", "source": "import numpy as np\nprint('hello')"},
        {"cell_type": "markdown", "source": "## Visualization"},
        {"cell_type": "code", "source": "import matplotlib.pyplot as plt\nplt.plot([1,2,3])"},
    ]


def test_returns_valid_notebook():
    nb = build_notebook(_sample_cells(), "Test Paper Title")
    # Should be valid nbformat
    nbformat.validate(nb)


def test_notebook_has_correct_nbformat():
    nb = build_notebook(_sample_cells(), "Test Paper Title")
    assert nb.nbformat == 4


def test_includes_colab_setup_cell_first():
    nb = build_notebook(_sample_cells(), "Test Paper Title")
    first_code_cell = None
    for cell in nb.cells:
        if cell.cell_type == "code":
            first_code_cell = cell
            break
    assert first_code_cell is not None
    assert "pip install" in first_code_cell.source or "!pip" in first_code_cell.source


def test_includes_title_cell():
    nb = build_notebook(_sample_cells(), "Test Paper Title")
    assert nb.cells[0].cell_type == "markdown"
    assert "Test Paper Title" in nb.cells[0].source


def test_includes_all_llm_cells():
    cells = _sample_cells()
    nb = build_notebook(cells, "Title")
    # Should have: title + setup + 4 LLM cells = 6 minimum
    assert len(nb.cells) >= len(cells) + 2


def test_has_colab_metadata():
    nb = build_notebook(_sample_cells(), "Title")
    assert "colab" in nb.metadata or "kernelspec" in nb.metadata


def test_serializes_to_valid_json():
    nb = build_notebook(_sample_cells(), "Title")
    json_str = nbformat.writes(nb)
    parsed = json.loads(json_str)
    assert "cells" in parsed
    assert "nbformat" in parsed
