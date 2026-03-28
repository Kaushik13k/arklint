"""Tests for --github-annotations flag on arklint check."""

import tempfile
import textwrap
from pathlib import Path

from typer.testing import CliRunner

from arklint.cli import app

runner = CliRunner()


def _make_project(code: str) -> tuple[Path, Path]:
    """Returns (config_path, scan_dir).

    The config lives in a separate directory so the scanner does not
    pick up the .arklint.yml file itself (which contains the pattern strings).
    """
    cfg_dir = Path(tempfile.mkdtemp())
    scan_dir = Path(tempfile.mkdtemp())

    cfg = cfg_dir / ".arklint.yml"
    cfg.write_text(
        textwrap.dedent(
            """\
        version: "1"
        rules:
          - id: no-print
            type: pattern-ban
            description: No print statements
            pattern: 'print\\('
            severity: warning
          - id: no-debugonly
            type: pattern-ban
            description: No debug-only markers
            pattern: "__debug_only__"
            severity: error
    """
        )
    )
    (scan_dir / "main.py").write_text(code)
    return cfg, scan_dir


class TestGithubAnnotations:
    def test_no_violations_emits_nothing(self):
        cfg, scan_dir = _make_project("x = 1\n")
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg), "--github-annotations"]
        )
        assert "::error" not in result.output
        assert "::warning" not in result.output

    def test_warning_violation_emits_warning_annotation(self):
        cfg, scan_dir = _make_project('print("hello")\n')
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg), "--github-annotations"]
        )
        assert "::warning" in result.output
        assert "no-print" in result.output

    def test_error_violation_emits_error_annotation(self):
        cfg, scan_dir = _make_project("x = __debug_only__\n")
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg), "--github-annotations"]
        )
        assert "::error" in result.output
        assert "no-debugonly" in result.output

    def test_annotation_includes_file_path(self):
        cfg, scan_dir = _make_project('print("hello")\n')
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg), "--github-annotations"]
        )
        assert "file=main.py" in result.output

    def test_annotation_includes_line_number(self):
        cfg, scan_dir = _make_project('x = 1\nprint("hello")\n')
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg), "--github-annotations"]
        )
        assert "line=2" in result.output

    def test_annotations_alongside_normal_output(self):
        """--github-annotations should not suppress normal report output."""
        cfg, scan_dir = _make_project('print("hello")\n')
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg), "--github-annotations"]
        )
        assert "WARN" in result.output
        assert "::warning" in result.output

    def test_without_flag_no_annotations(self):
        cfg, scan_dir = _make_project('print("hello")\n')
        result = runner.invoke(app, ["check", str(scan_dir), "--config", str(cfg)])
        assert "::warning" not in result.output
        assert "::error" not in result.output
