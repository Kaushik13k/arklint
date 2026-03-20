"""Tests for arklint visualize — Mermaid diagram generation."""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from arklint.cli import app
from arklint.config import ArklintConfig, RuleConfig
from arklint.visualize import build_mermaid, _safe_id


runner = CliRunner()


# ---------------------------------------------------------------------------
# _safe_id helper
# ---------------------------------------------------------------------------

class TestSafeId:
    def test_slashes_replaced(self):
        assert "/" not in _safe_id("routes/user")

    def test_hyphens_replaced(self):
        assert "-" not in _safe_id("layer-boundary")

    def test_dots_replaced(self):
        assert "." not in _safe_id("arklint.fastapi")

    def test_at_sign_replaced(self):
        assert "@" not in _safe_id("@angular/core")

    def test_plain_word_unchanged(self):
        assert _safe_id("routes") == "routes"


# ---------------------------------------------------------------------------
# build_mermaid — layer-boundary rules
# ---------------------------------------------------------------------------

def _make_cfg(rules: list[dict]) -> ArklintConfig:
    rule_cfgs = [
        RuleConfig(
            id=r["id"],
            type=r["type"],
            description=r.get("description", ""),
            severity=r.get("severity", "error"),
            raw=r,
        )
        for r in rules
    ]
    return ArklintConfig(version="1", rules=rule_cfgs)


class TestLayerBoundaryDiagram:
    def _cfg(self):
        return _make_cfg([{
            "id": "arch/layers",
            "type": "layer-boundary",
            "description": "Clean layers",
            "layers": [
                {"name": "routes", "path": "routes/**"},
                {"name": "services", "path": "services/**"},
                {"name": "repositories", "path": "repositories/**"},
            ],
            "allowed_dependencies": {
                "routes": ["services"],
                "services": ["repositories"],
                "repositories": [],
            },
            "severity": "error",
        }])

    def test_output_starts_with_flowchart(self):
        diagram = build_mermaid(self._cfg())
        assert diagram.startswith("flowchart LR")

    def test_layer_nodes_present(self):
        diagram = build_mermaid(self._cfg())
        assert "routes" in diagram
        assert "services" in diagram
        assert "repositories" in diagram

    def test_allowed_arrow_present(self):
        diagram = build_mermaid(self._cfg())
        # routes → services is allowed
        assert "routes --> services" in diagram

    def test_blocked_edge_present(self):
        diagram = build_mermaid(self._cfg())
        # routes → repositories is blocked
        assert "routes" in diagram and "blocked" in diagram

    def test_subgraph_uses_rule_description(self):
        diagram = build_mermaid(self._cfg())
        assert "Clean layers" in diagram

    def test_layer_path_shown_in_label(self):
        diagram = build_mermaid(self._cfg())
        assert "routes/**" in diagram


# ---------------------------------------------------------------------------
# build_mermaid — boundary rules
# ---------------------------------------------------------------------------

class TestBoundaryDiagram:
    def _cfg(self):
        return _make_cfg([{
            "id": "arch/no-db-in-routes",
            "type": "boundary",
            "description": "No DB in routes",
            "source": "routes/**",
            "blocked_imports": ["sqlalchemy", "psycopg2"],
            "severity": "error",
        }])

    def test_source_node_present(self):
        diagram = build_mermaid(self._cfg())
        assert "routes" in diagram

    def test_blocked_package_present(self):
        diagram = build_mermaid(self._cfg())
        assert "sqlalchemy" in diagram
        assert "psycopg2" in diagram

    def test_blocked_edge_present(self):
        diagram = build_mermaid(self._cfg())
        assert "blocked" in diagram

    def test_subgraph_label(self):
        diagram = build_mermaid(self._cfg())
        assert "Import boundaries" in diagram


# ---------------------------------------------------------------------------
# build_mermaid — dependency rules
# ---------------------------------------------------------------------------

class TestDependencyDiagram:
    def _cfg(self):
        return _make_cfg([{
            "id": "arch/single-http",
            "type": "dependency",
            "description": "One HTTP client",
            "allow_only_one_of": ["httpx", "requests", "aiohttp"],
            "severity": "warning",
        }])

    def test_packages_present(self):
        diagram = build_mermaid(self._cfg())
        assert "httpx" in diagram
        assert "requests" in diagram
        assert "aiohttp" in diagram

    def test_choose_one_node_present(self):
        diagram = build_mermaid(self._cfg())
        assert "choose one" in diagram

    def test_subgraph_label(self):
        diagram = build_mermaid(self._cfg())
        assert "Dependency constraints" in diagram


# ---------------------------------------------------------------------------
# build_mermaid — empty / unknown rules
# ---------------------------------------------------------------------------

class TestEmptyConfig:
    def test_no_rules_shows_comment(self):
        cfg = _make_cfg([])
        diagram = build_mermaid(cfg)
        assert "no visualisable" in diagram

    def test_pattern_ban_not_visualised(self):
        cfg = _make_cfg([{
            "id": "x/no-print",
            "type": "pattern-ban",
            "description": "No print",
            "pattern": r"print\(",
            "severity": "warning",
        }])
        diagram = build_mermaid(cfg)
        assert "no visualisable" in diagram


# ---------------------------------------------------------------------------
# CLI: arklint visualize
# ---------------------------------------------------------------------------

class TestVisualizeCLI:
    def _write_config(self, tmp_path: Path) -> Path:
        cfg = tmp_path / ".arklint.yml"
        cfg.write_text("""\
version: "1"
rules:
  - id: arch/layers
    type: layer-boundary
    description: Clean layers
    layers:
      - name: routes
        path: "routes/**"
      - name: services
        path: "services/**"
    allowed_dependencies:
      routes: [services]
      services: []
    severity: error
""")
        return cfg

    def test_visualize_prints_mermaid(self, tmp_path):
        cfg = self._write_config(tmp_path)
        result = runner.invoke(app, ["visualize", "--config", str(cfg)])
        assert result.exit_code == 0
        assert "flowchart LR" in result.output

    def test_visualize_output_file(self, tmp_path):
        cfg = self._write_config(tmp_path)
        out = tmp_path / "diagram.md"
        result = runner.invoke(app, ["visualize", "--config", str(cfg), "--output", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        assert "flowchart LR" in out.read_text()

    def test_visualize_missing_config_exits_1(self, tmp_path):
        result = runner.invoke(app, ["visualize", "--config", str(tmp_path / "missing.yml")])
        assert result.exit_code == 1
