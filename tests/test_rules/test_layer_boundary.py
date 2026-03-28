"""Tests for LayerBoundaryRule."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pathspec

from arklint.config import RuleConfig
from arklint.rules.layer_boundary import (
    LayerBoundaryRule,
    _import_to_layer,
    _match_layer,
)

# ── helpers ───────────────────────────────────────────────────────────────────

LAYERS = [
    {"name": "routes", "path": "routes/**"},
    {"name": "services", "path": "services/**"},
    {"name": "repositories", "path": "repositories/**"},
]

ALLOWED = {
    "routes": ["services"],
    "services": ["repositories"],
    "repositories": [],
}


def _make_rule(
    layers: list[dict] = LAYERS,
    allowed: dict = ALLOWED,
    root: Path | None = None,
) -> LayerBoundaryRule:
    raw = {
        "id": "test/layer-boundary",
        "type": "layer-boundary",
        "description": "Test layer rule",
        "layers": layers,
        "allowed_dependencies": allowed,
        "severity": "error",
    }
    cfg = RuleConfig(
        id="test/layer-boundary",
        type="layer-boundary",
        description="Test layer rule",
        severity="error",
        raw=raw,
    )
    return LayerBoundaryRule(config=cfg, root=root or Path("/repo"))


def _write(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content))
    return p


# ── _match_layer helper ───────────────────────────────────────────────────────


class TestMatchLayer:
    def _specs(self):
        return {
            name: pathspec.PathSpec.from_lines("gitignore", [layer["path"]])
            for name, layer in zip(
                ["routes", "services", "repositories"],
                LAYERS,
            )
        }

    def test_matches_routes(self):
        specs = self._specs()
        assert _match_layer("routes/user.py", specs) == "routes"

    def test_matches_services(self):
        specs = self._specs()
        assert _match_layer("services/user.py", specs) == "services"

    def test_no_match_returns_none(self):
        specs = self._specs()
        assert _match_layer("utils/helper.py", specs) is None

    def test_nested_path_matches(self):
        specs = self._specs()
        assert _match_layer("routes/v1/user.py", specs) == "routes"


# ── _import_to_layer helper ───────────────────────────────────────────────────


class TestImportToLayer:
    def _specs(self):
        return {
            name: pathspec.PathSpec.from_lines("gitignore", [layer["path"]])
            for name, layer in zip(
                ["routes", "services", "repositories"],
                LAYERS,
            )
        }

    def test_dotted_import_maps_to_layer(self):
        specs = self._specs()
        assert _import_to_layer("services.user", specs) == "services"

    def test_unrecognized_import_returns_none(self):
        specs = self._specs()
        assert _import_to_layer("os.path", specs) is None

    def test_top_level_import_maps(self):
        specs = self._specs()
        assert _import_to_layer("repositories", specs) == "repositories"


# ── allowed imports ───────────────────────────────────────────────────────────


class TestAllowedImports:
    def test_routes_importing_services_passes(self, tmp_path):
        f = _write(tmp_path, "routes/user.py", "from services import user_service\n")
        rule = _make_rule(root=tmp_path)
        assert rule.check([f]) == []

    def test_services_importing_repositories_passes(self, tmp_path):
        f = _write(tmp_path, "services/user.py", "from repositories import user_repo\n")
        rule = _make_rule(root=tmp_path)
        assert rule.check([f]) == []

    def test_intra_layer_import_passes(self, tmp_path):
        f = _write(tmp_path, "services/order.py", "from services import user_service\n")
        rule = _make_rule(root=tmp_path)
        assert rule.check([f]) == []

    def test_external_import_ignored(self, tmp_path):
        f = _write(tmp_path, "routes/user.py", "import os\nimport json\n")
        rule = _make_rule(root=tmp_path)
        assert rule.check([f]) == []


# ── violations ────────────────────────────────────────────────────────────────


class TestViolations:
    def test_routes_importing_repositories_violates(self, tmp_path):
        f = _write(tmp_path, "routes/user.py", "from repositories import user_repo\n")
        rule = _make_rule(root=tmp_path)
        violations = rule.check([f])
        assert len(violations) == 1
        assert "routes" in violations[0].message
        assert "repositories" in violations[0].message

    def test_services_importing_routes_violates(self, tmp_path):
        f = _write(tmp_path, "services/user.py", "from routes import api\n")
        rule = _make_rule(root=tmp_path)
        violations = rule.check([f])
        assert len(violations) == 1

    def test_repositories_importing_anything_violates(self, tmp_path):
        f = _write(tmp_path, "repositories/user.py", "from services import svc\n")
        rule = _make_rule(root=tmp_path)
        violations = rule.check([f])
        assert len(violations) == 1

    def test_violation_deduplicated_per_layer_pair(self, tmp_path):
        # Two imports from same disallowed layer → one violation per pair
        f = _write(
            tmp_path,
            "routes/user.py",
            ("from repositories import user_repo\nfrom repositories import order_repo\n"),
        )
        rule = _make_rule(root=tmp_path)
        violations = rule.check([f])
        assert len(violations) == 1

    def test_violation_message_lists_allowed_deps(self, tmp_path):
        f = _write(tmp_path, "routes/user.py", "from repositories import user_repo\n")
        rule = _make_rule(root=tmp_path)
        violations = rule.check([f])
        assert "services" in violations[0].message


# ── edge cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_files_list(self, tmp_path):
        rule = _make_rule(root=tmp_path)
        assert rule.check([]) == []

    def test_file_not_in_any_layer_ignored(self, tmp_path):
        f = _write(tmp_path, "utils/helper.py", "from repositories import repo\n")
        rule = _make_rule(root=tmp_path)
        assert rule.check([f]) == []

    def test_no_layers_configured_returns_empty(self, tmp_path):
        f = _write(tmp_path, "routes/user.py", "from repositories import repo\n")
        rule = _make_rule(layers=[], allowed={}, root=tmp_path)
        assert rule.check([f]) == []

    def test_clean_project_no_violations(self, tmp_path):
        routes = _write(tmp_path, "routes/user.py", "from services import user_svc\n")
        services = _write(tmp_path, "services/user.py", "from repositories import user_repo\n")
        repos = _write(tmp_path, "repositories/user.py", "import json\n")
        rule = _make_rule(root=tmp_path)
        assert rule.check([routes, services, repos]) == []

    def test_multiple_files_multiple_violations(self, tmp_path):
        f1 = _write(tmp_path, "routes/user.py", "from repositories import repo\n")
        f2 = _write(tmp_path, "services/order.py", "from routes import api\n")
        rule = _make_rule(root=tmp_path)
        assert len(rule.check([f1, f2])) == 2
