"""Layer-boundary rule - enforce a strict layered architecture.

Example config::

    - id: layered-arch
      type: layer-boundary
      description: "routes → services → repositories only"
      layers:
        - name: routes
          path: "routes/**"
        - name: services
          path: "services/**"
        - name: repositories
          path: "repositories/**"
      allowed_dependencies:
        routes: [services]
        services: [repositories]
        repositories: []
      severity: error
"""
from __future__ import annotations

from pathlib import Path

import pathspec

from .base import BaseRule, Violation
from arklint.parsers.imports import extract_imports


class LayerBoundaryRule(BaseRule):
    """Prevent layers from importing from layers they are not allowed to depend on."""

    def check(self, files: list[Path]) -> list[Violation]:
        raw = self.config.raw
        layers_config: list[dict] = raw.get("layers", [])
        allowed_deps: dict[str, list[str]] = raw.get(
            "allowed_dependencies", {})

        if not layers_config:
            return []

        # Build  name → pathspec  mapping
        layer_specs: dict[str, pathspec.PathSpec] = {
            layer["name"]: pathspec.PathSpec.from_lines(
                "gitignore",
                [layer["path"]] if isinstance(
                    layer["path"], str) else layer["path"],
            )
            for layer in layers_config
            if layer.get("name") and layer.get("path")
        }

        violations: list[Violation] = []
        # Track (file, source_layer, target_layer) to avoid duplicate messages
        seen: set[tuple[Path, str, str]] = set()

        for file in files:
            rel = self._rel(file)
            source_layer = _match_layer(rel, layer_specs)
            if source_layer is None:
                continue

            permitted: list[str] = allowed_deps.get(source_layer, [])

            for imp in extract_imports(file):
                target_layer = _import_to_layer(imp, layer_specs)
                if target_layer is None or target_layer == source_layer:
                    continue
                if target_layer in permitted:
                    continue

                key = (file, source_layer, target_layer)
                if key in seen:
                    continue
                seen.add(key)

                violations.append(
                    self._violation(
                        file=file,
                        line=None,
                        message=(
                            f"layer '{source_layer}' must not import from '{target_layer}'. "
                            f"Allowed dependencies: {permitted or ['(none)']}"
                        ),
                    )
                )

        return violations


# ---------------------------------------------------------------------------
# Helpers (module-level to keep the class small)
# ---------------------------------------------------------------------------

def _match_layer(rel_path: str, specs: dict[str, pathspec.PathSpec]) -> str | None:
    for name, spec in specs.items():
        if spec.match_file(rel_path):
            return name
    return None


def _import_to_layer(imp: str, specs: dict[str, pathspec.PathSpec]) -> str | None:
    # Heuristic: convert dotted Python import to a path and match against layer globs.
    # "services.users" → try "services/users", "services/users.py", "services/users/__init__.py"
    as_path = imp.replace(".", "/")
    for name, spec in specs.items():
        if (
            spec.match_file(as_path)
            or spec.match_file(as_path + ".py")
            or spec.match_file(as_path + "/__init__.py")
        ):
            return name
    return None
