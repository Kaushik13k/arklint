"""Tests for arklint learn command and learner module."""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from arklint.cli import app

runner = CliRunner()

FAKE_RULE_YAML = textwrap.dedent(
    """\
    - id: no-raw-sql
      type: pattern-ban
      description: No raw SQL queries in route handlers
      pattern: 'execute\\('
      severity: error
"""
).strip()


def _mock_suggest(monkeypatch, return_value: str = FAKE_RULE_YAML) -> None:
    """Patch learner.suggest_rule to return *return_value* without an API call."""
    monkeypatch.setattr(
        "arklint.learner.suggest_rule",
        lambda description, provider, api_key=None: return_value,
    )


def _make_config(tmp_dir: Path) -> Path:
    cfg = tmp_dir / ".arklint.yml"
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
    """
        )
    )
    return cfg


def _fake_anthropic_module(monkeypatch, response_text: str) -> None:
    fake_msg = MagicMock()
    fake_msg.content = [MagicMock(text=response_text)]
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_msg
    fake_anthropic = MagicMock()
    fake_anthropic.Anthropic.return_value = fake_client
    monkeypatch.setitem(__import__("sys").modules, "anthropic", fake_anthropic)


def _fake_openai_module(monkeypatch, response_text: str) -> None:
    fake_choice = MagicMock()
    fake_choice.message.content = response_text
    fake_response = MagicMock()
    fake_response.choices = [fake_choice]
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_response
    fake_openai = MagicMock()
    fake_openai.OpenAI.return_value = fake_client
    monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai)


# ---------------------------------------------------------------------------
# learner module unit tests
# ---------------------------------------------------------------------------


class TestSuggestRule:
    def test_unknown_provider_raises_value_error(self):
        from arklint.learner import suggest_rule

        with pytest.raises(ValueError, match="Unknown provider"):
            suggest_rule("something", provider="copilot")

    def test_anthropic_raises_import_error_without_package(self, monkeypatch):
        monkeypatch.setitem(__import__("sys").modules, "anthropic", None)
        import importlib

        from arklint import learner

        importlib.reload(learner)
        with pytest.raises(ImportError, match="anthropic"):
            learner.suggest_rule("test", provider="anthropic", api_key="sk-x")

    def test_openai_raises_import_error_without_package(self, monkeypatch):
        monkeypatch.setitem(__import__("sys").modules, "openai", None)
        import importlib

        from arklint import learner

        importlib.reload(learner)
        with pytest.raises(ImportError, match="openai"):
            learner.suggest_rule("test", provider="openai", api_key="sk-x")

    def test_anthropic_raises_value_error_without_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        _fake_anthropic_module(monkeypatch, FAKE_RULE_YAML)
        import importlib

        from arklint import learner

        importlib.reload(learner)
        with pytest.raises(ValueError, match="Anthropic API key"):
            learner.suggest_rule("no raw sql", provider="anthropic", api_key=None)

    def test_openai_raises_value_error_without_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        _fake_openai_module(monkeypatch, FAKE_RULE_YAML)
        import importlib

        from arklint import learner

        importlib.reload(learner)
        with pytest.raises(ValueError, match="OpenAI API key"):
            learner.suggest_rule("no raw sql", provider="openai", api_key=None)

    def test_anthropic_returns_yaml_snippet(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        _fake_anthropic_module(monkeypatch, FAKE_RULE_YAML)
        import importlib

        from arklint import learner

        importlib.reload(learner)
        result = learner.suggest_rule("no raw sql", provider="anthropic", api_key="sk-test")
        assert result.startswith("- id:")
        assert "no-raw-sql" in result

    def test_openai_returns_yaml_snippet(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        _fake_openai_module(monkeypatch, FAKE_RULE_YAML)
        import importlib

        from arklint import learner

        importlib.reload(learner)
        result = learner.suggest_rule("no raw sql", provider="openai", api_key="sk-test")
        assert result.startswith("- id:")
        assert "no-raw-sql" in result

    def test_raises_runtime_error_on_bad_response(self, monkeypatch):
        _fake_anthropic_module(monkeypatch, "Sorry, I cannot help.")
        import importlib

        from arklint import learner

        importlib.reload(learner)
        with pytest.raises(RuntimeError, match="Unexpected response"):
            learner.suggest_rule("something", provider="anthropic", api_key="sk-test")


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


class TestLearnCLI:
    def test_invalid_provider_exits_1(self, monkeypatch, tmp_path):
        _mock_suggest(monkeypatch)
        cfg = _make_config(tmp_path)
        result = runner.invoke(
            app,
            [
                "learn",
                "--describe",
                "no raw sql",
                "--config",
                str(cfg),
                "--provider",
                "copilot",
                "--api-key",
                "sk-test",
            ],
        )
        assert result.exit_code == 1
        assert "Unknown provider" in result.output

    def test_anthropic_provider_passed_through(self, monkeypatch, tmp_path):
        captured = {}

        def fake_suggest(description, provider, api_key=None):
            captured["provider"] = provider
            return FAKE_RULE_YAML

        monkeypatch.setattr("arklint.learner.suggest_rule", fake_suggest)
        cfg = _make_config(tmp_path)
        runner.invoke(
            app,
            [
                "learn",
                "--describe",
                "no raw sql",
                "--config",
                str(cfg),
                "--provider",
                "anthropic",
                "--api-key",
                "sk-test",
            ],
            input="n\n",
        )
        assert captured.get("provider") == "anthropic"

    def test_openai_provider_passed_through(self, monkeypatch, tmp_path):
        captured = {}

        def fake_suggest(description, provider, api_key=None):
            captured["provider"] = provider
            return FAKE_RULE_YAML

        monkeypatch.setattr("arklint.learner.suggest_rule", fake_suggest)
        cfg = _make_config(tmp_path)
        runner.invoke(
            app,
            [
                "learn",
                "--describe",
                "no raw sql",
                "--config",
                str(cfg),
                "--provider",
                "openai",
                "--api-key",
                "sk-test",
            ],
            input="n\n",
        )
        assert captured.get("provider") == "openai"

    def test_shows_suggested_rule(self, monkeypatch, tmp_path):
        _mock_suggest(monkeypatch)
        cfg = _make_config(tmp_path)
        result = runner.invoke(
            app,
            [
                "learn",
                "--describe",
                "no raw sql",
                "--config",
                str(cfg),
                "--provider",
                "anthropic",
                "--api-key",
                "sk-test",
            ],
            input="n\n",
        )
        assert "no-raw-sql" in result.output

    def test_decline_does_not_modify_config(self, monkeypatch, tmp_path):
        _mock_suggest(monkeypatch)
        cfg = _make_config(tmp_path)
        original = cfg.read_text()
        runner.invoke(
            app,
            [
                "learn",
                "--describe",
                "no raw sql",
                "--config",
                str(cfg),
                "--provider",
                "anthropic",
                "--api-key",
                "sk-test",
            ],
            input="n\n",
        )
        assert cfg.read_text() == original

    def test_append_flag_writes_to_config(self, monkeypatch, tmp_path):
        _mock_suggest(monkeypatch)
        cfg = _make_config(tmp_path)
        result = runner.invoke(
            app,
            [
                "learn",
                "--describe",
                "no raw sql",
                "--config",
                str(cfg),
                "--provider",
                "anthropic",
                "--api-key",
                "sk-test",
                "--append",
            ],
        )
        assert result.exit_code == 0
        assert "no-raw-sql" in cfg.read_text()

    def test_confirm_yes_writes_to_config(self, monkeypatch, tmp_path):
        _mock_suggest(monkeypatch)
        cfg = _make_config(tmp_path)
        result = runner.invoke(
            app,
            [
                "learn",
                "--describe",
                "no raw sql",
                "--config",
                str(cfg),
                "--provider",
                "anthropic",
                "--api-key",
                "sk-test",
            ],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "no-raw-sql" in cfg.read_text()

    def test_success_message_shown(self, monkeypatch, tmp_path):
        _mock_suggest(monkeypatch)
        cfg = _make_config(tmp_path)
        result = runner.invoke(
            app,
            [
                "learn",
                "--describe",
                "no raw sql",
                "--config",
                str(cfg),
                "--provider",
                "anthropic",
                "--api-key",
                "sk-test",
                "--append",
            ],
        )
        assert "appended" in result.output.lower()

    def test_append_produces_valid_yaml(self, monkeypatch, tmp_path):
        import yaml

        _mock_suggest(monkeypatch)
        cfg = _make_config(tmp_path)
        runner.invoke(
            app,
            [
                "learn",
                "--describe",
                "no raw sql",
                "--config",
                str(cfg),
                "--provider",
                "anthropic",
                "--api-key",
                "sk-test",
                "--append",
            ],
        )
        parsed = yaml.safe_load(cfg.read_text())
        assert isinstance(parsed, dict)

    def test_append_rule_is_structurally_correct(self, monkeypatch, tmp_path):
        import yaml

        _mock_suggest(monkeypatch)
        cfg = _make_config(tmp_path)
        runner.invoke(
            app,
            [
                "learn",
                "--describe",
                "no raw sql",
                "--config",
                str(cfg),
                "--provider",
                "anthropic",
                "--api-key",
                "sk-test",
                "--append",
            ],
        )
        parsed = yaml.safe_load(cfg.read_text())
        rule_ids = [r["id"] for r in parsed["rules"]]
        assert "no-raw-sql" in rule_ids

    def test_append_preserves_existing_rules(self, monkeypatch, tmp_path):
        import yaml

        _mock_suggest(monkeypatch)
        cfg = _make_config(tmp_path)
        runner.invoke(
            app,
            [
                "learn",
                "--describe",
                "no raw sql",
                "--config",
                str(cfg),
                "--provider",
                "anthropic",
                "--api-key",
                "sk-test",
                "--append",
            ],
        )
        parsed = yaml.safe_load(cfg.read_text())
        rule_ids = [r["id"] for r in parsed["rules"]]
        assert "no-print" in rule_ids
        assert "no-raw-sql" in rule_ids
