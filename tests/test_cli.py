"""Tests for CLI commands: validate and --quiet flag."""
import textwrap
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from arklint.cli import app

runner = CliRunner()


def _write_config(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".yml", delete=False, mode="w")
    tmp.write(textwrap.dedent(content))
    tmp.close()
    return Path(tmp.name)


# ---------------------------------------------------------------------------
# arklint validate
# ---------------------------------------------------------------------------

class TestValidate:
    def test_valid_config_exits_0(self):
        cfg = _write_config("""
            version: "1"
            rules:
              - id: no-print
                type: pattern-ban
                description: No print
                pattern: "print\\\\("
                severity: warning
        """)
        result = runner.invoke(app, ["validate", "--config", str(cfg)])
        assert result.exit_code == 0
        assert "Valid" in result.output

    def test_valid_config_shows_rule_count(self):
        cfg = _write_config("""
            version: "1"
            rules:
              - id: no-print
                type: pattern-ban
                description: No print
                pattern: "print\\\\("
                severity: warning
              - id: no-todo
                type: pattern-ban
                description: No TODO
                pattern: "TODO"
                severity: error
        """)
        result = runner.invoke(app, ["validate", "--config", str(cfg)])
        assert result.exit_code == 0
        assert "2 rules" in result.output

    def test_invalid_config_exits_1(self):
        cfg = _write_config("""
            version: "1"
            rules:
              - type: pattern-ban
                pattern: "print\\\\("
        """)
        result = runner.invoke(app, ["validate", "--config", str(cfg)])
        assert result.exit_code == 1

    def test_missing_config_exits_1(self):
        result = runner.invoke(
            app, ["validate", "--config", "/nonexistent/.arklint.yml"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# arklint check --quiet
# ---------------------------------------------------------------------------

class TestQuiet:
    def _make_project(self, code: str) -> tuple[Path, Path]:
        """Returns (config_path, py_file_path)."""
        tmp_dir = Path(tempfile.mkdtemp())
        cfg = tmp_dir / ".arklint.yml"
        cfg.write_text(textwrap.dedent("""
            version: "1"
            rules:
              - id: no-print
                type: pattern-ban
                description: No print
                pattern: 'print\\('
                severity: warning
              - id: no-todo
                type: pattern-ban
                description: No TODO
                pattern: "TODO"
                severity: error
        """))
        py_file = tmp_dir / "main.py"
        py_file.write_text(code)
        return cfg, tmp_dir

    def test_quiet_suppresses_passing_rules(self):
        cfg, scan_dir = self._make_project("x = 1\n")
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg), "--quiet"])
        assert "PASS" not in result.output

    def test_quiet_still_shows_violations(self):
        cfg, scan_dir = self._make_project('print("bad")\n')
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg), "--quiet"])
        assert "WARN" in result.output or "FAIL" in result.output

    def test_without_quiet_shows_passing_rules(self):
        cfg, scan_dir = self._make_project("x = 1\n")
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg)])
        assert "PASS" in result.output


# ---------------------------------------------------------------------------
# arklint check - status line and exit codes
# ---------------------------------------------------------------------------

class TestCheckStatusLine:
    def _make_project(self, code: str, severity: str = "warning") -> tuple[Path, Path]:
        tmp_dir = Path(tempfile.mkdtemp())
        cfg = tmp_dir / ".arklint.yml"
        cfg.write_text(textwrap.dedent(f"""
            version: "1"
            rules:
              - id: no-print
                type: pattern-ban
                description: No print
                pattern: 'print\\('
                severity: {severity}
        """))
        (tmp_dir / "main.py").write_text(code)
        return cfg, tmp_dir

    def test_clean_shows_all_rules_passed(self):
        cfg, scan_dir = self._make_project("x = 1\n")
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg)])
        assert result.exit_code == 0
        assert "all rules passed" in result.output

    def test_warning_without_strict_exits_0(self):
        cfg, scan_dir = self._make_project('print("hi")\n', severity="warning")
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg)])
        assert result.exit_code == 0

    def test_warning_without_strict_shows_warning_message(self):
        cfg, scan_dir = self._make_project('print("hi")\n', severity="warning")
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg)])
        assert "warnings" in result.output.lower()
        assert "all rules passed" not in result.output

    def test_warning_with_strict_exits_1(self):
        cfg, scan_dir = self._make_project('print("hi")\n', severity="warning")
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg), "--strict"])
        assert result.exit_code == 1

    def test_warning_with_strict_shows_strict_message(self):
        cfg, scan_dir = self._make_project('print("hi")\n', severity="warning")
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg), "--strict"])
        assert "strict" in result.output.lower()

    def test_error_exits_1(self):
        cfg, scan_dir = self._make_project('print("hi")\n', severity="error")
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg)])
        assert result.exit_code == 1

    def test_error_shows_violations_message(self):
        cfg, scan_dir = self._make_project('print("hi")\n', severity="error")
        result = runner.invoke(
            app, ["check", str(scan_dir), "--config", str(cfg)])
        assert "violations" in result.output.lower()
        assert "all rules passed" not in result.output
