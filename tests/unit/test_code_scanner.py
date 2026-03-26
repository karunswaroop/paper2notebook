"""Unit tests for code cell safety scanner (Task 3, Findings F1, F5)."""
import pytest

from backend.services.notebook_builder import scan_code_cell

WARNING_PREFIX = "# WARNING: This cell contains potentially unsafe code. Review before running."


class TestDangerousPatterns:
    """Each dangerous pattern should be flagged."""

    def test_os_system(self):
        flags = scan_code_cell('os.system("rm -rf /")')
        assert "os.system" in flags

    def test_subprocess(self):
        flags = scan_code_cell("subprocess.run(['ls'])")
        assert "subprocess" in flags

    def test_eval(self):
        flags = scan_code_cell('eval("1+1")')
        assert "eval(" in flags

    def test_exec(self):
        flags = scan_code_cell('exec("print(1)")')
        assert "exec(" in flags

    def test_dunder_import(self):
        flags = scan_code_cell('__import__("os")')
        assert "__import__" in flags

    def test_compile(self):
        flags = scan_code_cell('compile("code", "f", "exec")')
        assert "compile(" in flags

    def test_open_write(self):
        flags = scan_code_cell('open("/etc/passwd", "w")')
        assert "open(" in flags

    def test_requests(self):
        flags = scan_code_cell('requests.get("http://evil.com")')
        assert "requests." in flags

    def test_urllib(self):
        flags = scan_code_cell("urllib.request.urlopen('http://evil.com')")
        assert "urllib" in flags

    def test_socket(self):
        flags = scan_code_cell("s = socket.socket()")
        assert "socket" in flags

    def test_shutil_rmtree(self):
        flags = scan_code_cell('shutil.rmtree("/")')
        assert "shutil.rmtree" in flags


class TestSafePatterns:
    """Normal code should not be flagged."""

    def test_numpy_code(self):
        flags = scan_code_cell("import numpy as np\nx = np.array([1, 2, 3])")
        assert flags == []

    def test_matplotlib_code(self):
        flags = scan_code_cell("import matplotlib.pyplot as plt\nplt.plot([1,2,3])\nplt.show()")
        assert flags == []

    def test_print_statement(self):
        flags = scan_code_cell('print("hello world")')
        assert flags == []

    def test_open_read(self):
        # open() in read mode should not be flagged
        flags = scan_code_cell('open("file.txt", "r")')
        assert flags == []

    def test_open_default_mode(self):
        # open() without explicit write mode should not be flagged
        flags = scan_code_cell('data = open("file.txt").read()')
        assert flags == []


class TestWarningPrepend:
    """Flagged cells should get the warning comment prepended."""

    def test_warning_added_to_flagged_cell(self):
        from backend.services.notebook_builder import build_notebook
        cells = [{"cell_type": "code", "source": 'os.system("bad")'}]
        nb = build_notebook(cells, "Test")
        # Find the LLM-generated code cell (skip the setup cell)
        code_cells = [c for c in nb.cells if c.cell_type == "code"]
        flagged = [c for c in code_cells if WARNING_PREFIX in c.source]
        assert len(flagged) >= 1

    def test_no_warning_on_safe_cell(self):
        from backend.services.notebook_builder import build_notebook
        cells = [{"cell_type": "code", "source": "x = 1 + 2"}]
        nb = build_notebook(cells, "Test")
        code_cells = [c for c in nb.cells if c.cell_type == "code"]
        for c in code_cells:
            if "x = 1 + 2" in c.source:
                assert WARNING_PREFIX not in c.source
