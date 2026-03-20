"""Tests for packs.py (extends system) and the search/add CLI commands."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

import pytest
import yaml
from typer.testing import CliRunner

from arklint.cli import app
from arklint.packs import (
    PackError,
    _extract_rules,
    resolve_pack,
    search_packs,
)

runner = CliRunner()

# ── helpers ───────────────────────────────────────────────────────────────────

SIMPLE_PACK = textwrap.dedent("""\
    name: test/simple
    version: "1"
    rules:
      - id: test/no-print
        type: pattern-ban
        description: No print statements
        pattern: 'print\\('
        severity: warning
""")

REGISTRY_DATA = {
    "packs": [
        {
            "name": "arklint/fastapi",
            "description": "FastAPI best practices",
            "tags": ["python", "fastapi"],
            "rules": 4,
        },
        {
            "name": "arklint/django",
            "description": "Django conventions",
            "tags": ["python", "django"],
            "rules": 4,
        },
    ]
}


def _make_local_pack(tmp_path: Path, content: str = SIMPLE_PACK) -> Path:
    pack_file = tmp_path / "my-pack.yml"
    pack_file.write_text(content)
    return pack_file


# ── _extract_rules ────────────────────────────────────────────────────────────

class TestExtractRules:
    def test_returns_rules_list(self):
        data = {"rules": [{"id": "r1", "type": "pattern-ban"}]}
        assert _extract_rules(data, "ref") == [
            {"id": "r1", "type": "pattern-ban"}]

    def test_empty_rules(self):
        assert _extract_rules({"rules": []}, "ref") == []

    def test_missing_rules_key_raises(self):
        with pytest.raises(PackError, match="must define a 'rules' key"):
            _extract_rules({}, "ref")

    def test_non_dict_raises(self):
        with pytest.raises(PackError, match="must be a YAML mapping"):
            _extract_rules("not a dict", "ref")

    def test_rules_not_list_raises(self):
        with pytest.raises(PackError, match="must be a list"):
            _extract_rules({"rules": "bad"}, "ref")


# ── resolve_pack — local ──────────────────────────────────────────────────────

class TestResolvePackLocal:
    def test_loads_local_pack(self, tmp_path):
        pack_file = _make_local_pack(tmp_path)
        rules = resolve_pack(f"./{pack_file.name}", tmp_path)
        assert len(rules) == 1
        assert rules[0]["id"] == "test/no-print"

    def test_missing_local_pack_raises(self, tmp_path):
        with pytest.raises(PackError, match="Local pack not found"):
            resolve_pack("./nonexistent.yml", tmp_path)

    def test_invalid_yaml_raises(self, tmp_path):
        bad = tmp_path / "bad.yml"
        bad.write_text("rules: [{{bad yaml")
        with pytest.raises(PackError, match="Invalid YAML"):
            resolve_pack("./bad.yml", tmp_path)

    def test_absolute_path_resolves(self, tmp_path):
        pack_file = _make_local_pack(tmp_path)
        rules = resolve_pack(str(pack_file), tmp_path)
        assert len(rules) == 1

    def test_parent_relative_path(self, tmp_path):
        subdir = tmp_path / "sub"
        subdir.mkdir()
        pack_file = _make_local_pack(tmp_path)
        rules = resolve_pack(f"../{pack_file.name}", subdir)
        assert len(rules) == 1


# ── resolve_pack — named (mocked network) ────────────────────────────────────

class TestResolvePackNamed:
    def test_fetches_named_pack(self, tmp_path):
        mock_resp = MagicMock()
        mock_resp.read.return_value = SIMPLE_PACK.encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("arklint.packs.urllib.request.urlopen", return_value=mock_resp), \
                patch("arklint.packs.PACKS_CACHE_DIR", tmp_path):
            rules = resolve_pack("arklint/fastapi", tmp_path)

        assert len(rules) == 1
        assert rules[0]["id"] == "test/no-print"

    def test_network_failure_raises(self, tmp_path):
        with patch("arklint.packs.urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")), \
                patch("arklint.packs.PACKS_CACHE_DIR", tmp_path):
            with pytest.raises(PackError, match="Could not fetch pack"):
                resolve_pack("arklint/fastapi", tmp_path)

    def test_uses_cache_on_second_call(self, tmp_path):
        cached = tmp_path / "cached.yml"
        cached.write_text(SIMPLE_PACK)

        with patch("arklint.packs._cache_path", return_value=cached):
            rules = resolve_pack("arklint/fastapi", tmp_path)

        assert len(rules) == 1


# ── search_packs ──────────────────────────────────────────────────────────────

class TestSearchPacks:
    def test_search_matches_name(self):
        with patch("arklint.packs.fetch_registry", return_value=REGISTRY_DATA):
            results = search_packs("fastapi")
        assert len(results) == 1
        assert results[0]["name"] == "arklint/fastapi"

    def test_search_matches_description(self):
        with patch("arklint.packs.fetch_registry", return_value=REGISTRY_DATA):
            results = search_packs("conventions")
        assert len(results) == 1
        assert results[0]["name"] == "arklint/django"

    def test_search_case_insensitive(self):
        with patch("arklint.packs.fetch_registry", return_value=REGISTRY_DATA):
            results = search_packs("FASTAPI")
        assert len(results) == 1

    def test_search_no_match(self):
        with patch("arklint.packs.fetch_registry", return_value=REGISTRY_DATA):
            results = search_packs("nonexistent")
        assert results == []

    def test_search_matches_multiple(self):
        with patch("arklint.packs.fetch_registry", return_value=REGISTRY_DATA):
            results = search_packs("python")
        assert len(results) == 2


# ── extends in config ─────────────────────────────────────────────────────────

class TestExtendsConfig:
    def test_extends_loads_pack_rules(self, tmp_path):
        pack_file = _make_local_pack(tmp_path)
        cfg_file = tmp_path / ".arklint.yml"
        cfg_file.write_text(textwrap.dedent(f"""\
            version: "1"
            extends:
              - ./{pack_file.name}
            rules: []
        """))

        from arklint.config import load_config
        cfg = load_config(cfg_file)
        assert any(r.id == "test/no-print" for r in cfg.rules)

    def test_local_rules_override_extended(self, tmp_path):
        pack_file = _make_local_pack(tmp_path)
        cfg_file = tmp_path / ".arklint.yml"
        cfg_file.write_text(textwrap.dedent(f"""\
            version: "1"
            extends:
              - ./{pack_file.name}
            rules:
              - id: test/no-print
                type: pattern-ban
                description: Overridden locally
                pattern: 'print\\('
                severity: error
        """))

        from arklint.config import load_config
        cfg = load_config(cfg_file)
        # only one rule with this id
        matching = [r for r in cfg.rules if r.id == "test/no-print"]
        assert len(matching) == 1
        assert matching[0].severity == "error"

    def test_extends_not_list_raises(self, tmp_path):
        cfg_file = tmp_path / ".arklint.yml"
        cfg_file.write_text(textwrap.dedent("""\
            version: "1"
            extends: "not-a-list"
            rules: []
        """))

        from arklint.config import load_config, ConfigError
        with pytest.raises(ConfigError, match="'extends' must be a list"):
            load_config(cfg_file)

    def test_bad_pack_ref_raises_config_error(self, tmp_path):
        cfg_file = tmp_path / ".arklint.yml"
        cfg_file.write_text(textwrap.dedent("""\
            version: "1"
            extends:
              - ./nonexistent.yml
            rules: []
        """))

        from arklint.config import load_config, ConfigError
        with pytest.raises(ConfigError, match="Failed to load pack"):
            load_config(cfg_file)

    def test_no_extends_still_works(self, tmp_path):
        cfg_file = tmp_path / ".arklint.yml"
        cfg_file.write_text(textwrap.dedent("""\
            version: "1"
            rules:
              - id: my-rule
                type: pattern-ban
                description: Test
                pattern: 'foo'
                severity: warning
        """))

        from arklint.config import load_config
        cfg = load_config(cfg_file)
        assert len(cfg.rules) == 1


# ── CLI: arklint search ───────────────────────────────────────────────────────

class TestSearchCommand:
    def test_search_shows_results(self):
        with patch("arklint.packs.fetch_registry", return_value=REGISTRY_DATA):
            result = runner.invoke(app, ["search", "fastapi"])
        assert result.exit_code == 0
        assert "arklint/fastapi" in result.output

    def test_search_no_results(self):
        with patch("arklint.packs.fetch_registry", return_value=REGISTRY_DATA):
            result = runner.invoke(app, ["search", "nonexistent"])
        assert result.exit_code == 0
        assert "No packs found" in result.output

    def test_search_registry_error(self):
        with patch("arklint.packs.fetch_registry", side_effect=PackError("timeout")):
            result = runner.invoke(app, ["search", "fastapi"])
        assert result.exit_code == 1
        assert "Registry error" in result.output


# ── CLI: arklint add ──────────────────────────────────────────────────────────

class TestAddCommand:
    def test_add_pack_to_config(self, tmp_path):
        pack_file = _make_local_pack(tmp_path)
        cfg_file = tmp_path / ".arklint.yml"
        cfg_file.write_text("version: '1'\nrules: []\n")

        result = runner.invoke(app, [
            "add", f"./{pack_file.name}",
            "--config", str(cfg_file),
        ])
        assert result.exit_code == 0
        content = cfg_file.read_text()
        assert pack_file.name in content

    def test_add_already_present(self, tmp_path):
        pack_file = _make_local_pack(tmp_path)
        cfg_file = tmp_path / ".arklint.yml"
        cfg_file.write_text(
            f"version: '1'\nextends:\n  - ./{pack_file.name}\nrules: []\n"
        )

        result = runner.invoke(app, [
            "add", f"./{pack_file.name}",
            "--config", str(cfg_file),
        ])
        assert result.exit_code == 0
        assert "already in extends" in result.output

    def test_add_missing_config(self, tmp_path):
        result = runner.invoke(app, [
            "add", "arklint/fastapi",
            "--config", str(tmp_path / ".arklint.yml"),
        ])
        assert result.exit_code == 1
