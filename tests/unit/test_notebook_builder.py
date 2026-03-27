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


# ---------------------------------------------------------------------------
# Malformed input and edge-case tests (Task 3, sprint v3)
# ---------------------------------------------------------------------------

_WARNING_COMMENT = (
    "# WARNING: This cell contains potentially unsafe code. Review before running."
)


class TestEmptyCellList:
    """Empty cell list should produce only the title + setup cells."""

    def test_empty_list_produces_two_cells(self):
        nb = build_notebook([], "My Paper")
        assert len(nb.cells) == 2

    def test_empty_list_first_cell_is_title(self):
        nb = build_notebook([], "My Paper")
        assert nb.cells[0].cell_type == "markdown"
        assert "My Paper" in nb.cells[0].source

    def test_empty_list_second_cell_is_setup(self):
        nb = build_notebook([], "My Paper")
        assert nb.cells[1].cell_type == "code"
        assert "pip install" in nb.cells[1].source

    def test_empty_list_is_valid_notebook(self):
        nb = build_notebook([], "My Paper")
        nbformat.validate(nb)


class TestMissingSourceKey:
    """Cell missing the `source` key should default to empty string."""

    def test_markdown_cell_missing_source(self):
        cells = [{"cell_type": "markdown"}]
        nb = build_notebook(cells, "T")
        # title + setup + 1 LLM cell
        assert len(nb.cells) == 3
        llm_cell = nb.cells[2]
        assert llm_cell.cell_type == "markdown"
        assert llm_cell.source == ""

    def test_code_cell_missing_source(self):
        cells = [{"cell_type": "code"}]
        nb = build_notebook(cells, "T")
        llm_cell = nb.cells[2]
        assert llm_cell.cell_type == "code"
        assert llm_cell.source == ""

    def test_missing_source_notebook_is_valid(self):
        cells = [{"cell_type": "code"}, {"cell_type": "markdown"}]
        nb = build_notebook(cells, "T")
        nbformat.validate(nb)


class TestMissingCellTypeKey:
    """Cell missing the `cell_type` key should default to 'markdown'."""

    def test_defaults_to_markdown(self):
        cells = [{"source": "Some text"}]
        nb = build_notebook(cells, "T")
        llm_cell = nb.cells[2]
        assert llm_cell.cell_type == "markdown"
        assert llm_cell.source == "Some text"

    def test_missing_cell_type_notebook_is_valid(self):
        cells = [{"source": "Some text"}]
        nb = build_notebook(cells, "T")
        nbformat.validate(nb)

    def test_missing_both_keys(self):
        """Cell with no keys at all should become an empty markdown cell."""
        cells = [{}]
        nb = build_notebook(cells, "T")
        llm_cell = nb.cells[2]
        assert llm_cell.cell_type == "markdown"
        assert llm_cell.source == ""


class TestRawCellType:
    """Cell with cell_type 'raw' should be treated as markdown."""

    def test_raw_becomes_markdown(self):
        cells = [{"cell_type": "raw", "source": "Raw content here"}]
        nb = build_notebook(cells, "T")
        llm_cell = nb.cells[2]
        assert llm_cell.cell_type == "markdown"
        assert llm_cell.source == "Raw content here"

    def test_raw_cell_not_scanned_for_danger(self):
        """Raw cells should not get a warning since they are not code."""
        cells = [{"cell_type": "raw", "source": 'os.system("bad")'}]
        nb = build_notebook(cells, "T")
        llm_cell = nb.cells[2]
        assert _WARNING_COMMENT not in llm_cell.source

    def test_raw_cell_notebook_is_valid(self):
        cells = [{"cell_type": "raw", "source": "text"}]
        nb = build_notebook(cells, "T")
        nbformat.validate(nb)


class TestVeryLongPaperTitle:
    """Paper title longer than 500 characters."""

    def test_long_title_in_title_cell(self):
        long_title = "A" * 600
        nb = build_notebook([], long_title)
        assert long_title in nb.cells[0].source

    def test_long_title_in_metadata(self):
        long_title = "A" * 600
        nb = build_notebook([], long_title)
        assert long_title in nb.metadata["colab"]["name"]

    def test_long_title_notebook_is_valid(self):
        long_title = "A" * 600
        nb = build_notebook([], long_title)
        nbformat.validate(nb)

    def test_long_title_serializes(self):
        long_title = "A" * 600
        nb = build_notebook([], long_title)
        json_str = nbformat.writes(nb)
        parsed = json.loads(json_str)
        # nbformat serializes source as a list of lines; join to check
        source = "".join(parsed["cells"][0]["source"])
        assert long_title in source


class TestMultipleDangerousPatternsInOneCell:
    """A single code cell containing multiple dangerous patterns should flag all."""

    def test_all_patterns_flagged(self):
        from backend.services.notebook_builder import scan_code_cell

        source = (
            'os.system("rm -rf /")\n'
            "subprocess.run(['ls'])\n"
            'eval("1+1")\n'
            'exec("print(1)")\n'
            '__import__("os")\n'
        )
        flags = scan_code_cell(source)
        assert "os.system" in flags
        assert "subprocess" in flags
        assert "eval(" in flags
        assert "exec(" in flags
        assert "__import__" in flags
        assert len(flags) == 5

    def test_warning_added_once_for_multi_pattern_cell(self):
        source = (
            'os.system("rm -rf /")\n'
            "subprocess.run(['ls'])\n"
            'eval("1+1")\n'
        )
        cells = [{"cell_type": "code", "source": source}]
        nb = build_notebook(cells, "T")
        llm_cell = nb.cells[2]
        # Warning comment appears exactly once
        assert llm_cell.source.count(_WARNING_COMMENT) == 1

    def test_multi_pattern_notebook_is_valid(self):
        source = (
            'os.system("x")\n'
            "subprocess.run(['y'])\n"
            'eval("z")\n'
        )
        cells = [{"cell_type": "code", "source": source}]
        nb = build_notebook(cells, "T")
        nbformat.validate(nb)


class TestSafeCellAlongsideDangerousCell:
    """A safe code cell and a dangerous code cell in the same notebook."""

    def test_safe_cell_no_warning(self):
        cells = [
            {"cell_type": "code", "source": "x = 1 + 2\nprint(x)"},
            {"cell_type": "code", "source": 'os.system("bad")\nsubprocess.run(["ls"])'},
        ]
        nb = build_notebook(cells, "T")
        # cells: title(0), setup(1), safe(2), dangerous(3)
        safe_cell = nb.cells[2]
        assert _WARNING_COMMENT not in safe_cell.source

    def test_dangerous_cell_has_warning(self):
        cells = [
            {"cell_type": "code", "source": "x = 1 + 2\nprint(x)"},
            {"cell_type": "code", "source": 'os.system("bad")\nsubprocess.run(["ls"])'},
        ]
        nb = build_notebook(cells, "T")
        dangerous_cell = nb.cells[3]
        assert _WARNING_COMMENT in dangerous_cell.source

    def test_both_cells_present(self):
        cells = [
            {"cell_type": "code", "source": "x = 1 + 2\nprint(x)"},
            {"cell_type": "code", "source": 'os.system("bad")\nsubprocess.run(["ls"])'},
        ]
        nb = build_notebook(cells, "T")
        # title + setup + 2 LLM cells = 4
        assert len(nb.cells) == 4

    def test_mixed_cells_notebook_is_valid(self):
        cells = [
            {"cell_type": "code", "source": "x = 1 + 2\nprint(x)"},
            {"cell_type": "code", "source": 'os.system("bad")\nsubprocess.run(["ls"])'},
        ]
        nb = build_notebook(cells, "T")
        nbformat.validate(nb)
