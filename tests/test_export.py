"""Tests for arklint export command and exporter module."""
import textwrap
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from arklint.cli import app
from arklint.config import load_config

runner = CliRunner()


def _write_config(tmp_dir: Path) -> Path:
    cfg = tmp_dir / ".arklint.yml"
    cfg.write_text(textwrap.dedent("""\
        version: "1"
        rules:
          - id: no-print
            type: pattern-ban
            description: No print statements allowed
            pattern: 'print\\('
            severity: warning
          - id: no-requests-in-models
            type: boundary
            description: Models must not import requests
            from_modules: ["models"]
            banned_imports: ["requests"]
            severity: error
    """))
    return cfg


class TestExportCLI:
    def test_invalid_format_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_config(Path(tmp))
            result = runner.invoke(app, ["export", "--format", "unknown", "--config", str(cfg)])
            assert result.exit_code == 1
            assert "Unknown format" in result.output

    def test_cursorrules_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_config(Path(tmp))
            result = runner.invoke(
                app, ["export", "--format", "cursorrules", "--config", str(cfg), "--output", tmp]
            )
            assert result.exit_code == 0

    def test_claude_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_config(Path(tmp))
            result = runner.invoke(
                app, ["export", "--format", "claude", "--config", str(cfg), "--output", tmp]
            )
            assert result.exit_code == 0

    def test_copilot_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_config(Path(tmp))
            result = runner.invoke(
                app, ["export", "--format", "copilot", "--config", str(cfg), "--output", tmp]
            )
            assert result.exit_code == 0

    def test_output_mentions_rule_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_config(Path(tmp))
            result = runner.invoke(
                app, ["export", "--format", "claude", "--config", str(cfg), "--output", tmp]
            )
            assert "2 rules" in result.output


class TestExportFiles:
    def test_cursorrules_written_to_correct_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_config(Path(tmp))
            runner.invoke(app, ["export", "--format", "cursorrules", "--config", str(cfg), "--output", tmp])
            assert (Path(tmp) / ".cursorrules").exists()

    def test_claude_written_to_correct_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_config(Path(tmp))
            runner.invoke(app, ["export", "--format", "claude", "--config", str(cfg), "--output", tmp])
            assert (Path(tmp) / "CLAUDE.md").exists()

    def test_copilot_written_to_correct_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_config(Path(tmp))
            runner.invoke(app, ["export", "--format", "copilot", "--config", str(cfg), "--output", tmp])
            assert (Path(tmp) / ".github" / "copilot-instructions.md").exists()

    def test_cursorrules_contains_rule_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_config(Path(tmp))
            runner.invoke(app, ["export", "--format", "cursorrules", "--config", str(cfg), "--output", tmp])
            content = (Path(tmp) / ".cursorrules").read_text()
            assert "no-print" in content
            assert "no-requests-in-models" in content

    def test_claude_contains_rule_descriptions(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_config(Path(tmp))
            runner.invoke(app, ["export", "--format", "claude", "--config", str(cfg), "--output", tmp])
            content = (Path(tmp) / "CLAUDE.md").read_text()
            assert "No print statements allowed" in content
            assert "Models must not import requests" in content

    def test_copilot_contains_severity_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_config(Path(tmp))
            runner.invoke(app, ["export", "--format", "copilot", "--config", str(cfg), "--output", tmp])
            content = (Path(tmp) / ".github" / "copilot-instructions.md").read_text()
            assert "[WARN]" in content
            assert "[ERROR]" in content
