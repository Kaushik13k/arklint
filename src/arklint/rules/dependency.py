"""Dependency rule - control what packages are allowed in the project.

Example config::

    - id: single-http-client
      type: dependency
      description: "Only one HTTP client library allowed"
      allow_only_one_of:
        - "requests"
        - "httpx"
        - "aiohttp"
      severity: error

    - id: no-pandas
      type: dependency
      description: "Use polars instead of pandas"
      banned:
        - "pandas"
      severity: error
"""

from __future__ import annotations

from pathlib import Path

from arklint.parsers.deps import parse_dependency_file

from .base import BaseRule, Violation

# File names that are considered dependency manifests
_DEP_FILENAMES: frozenset[str] = frozenset(
    {
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "requirements-prod.txt",
        "package.json",
        "pyproject.toml",
        "cargo.toml",
        "go.mod",
        "gemfile",
        "gemfile.lock",
    }
)


class DependencyRule(BaseRule):
    """Inspect dependency manifests for conflicting or banned packages."""

    def check(self, files: list[Path]) -> list[Violation]:
        raw = self.config.raw
        allow_only_one_of: list[str] = [p.lower() for p in raw.get("allow_only_one_of", [])]
        banned: list[str] = [p.lower() for p in raw.get("banned", [])]

        if not allow_only_one_of and not banned:
            return []

        # Aggregate packages → source files
        pkg_sources: dict[str, list[Path]] = {}
        for file in files:
            if file.name.lower() not in _DEP_FILENAMES:
                continue
            for pkg in parse_dependency_file(file):
                pkg_sources.setdefault(pkg, []).append(file)

        violations: list[Violation] = []

        if allow_only_one_of:
            found = [p for p in allow_only_one_of if p in pkg_sources]
            if len(found) > 1:
                source_names = sorted({self._rel(f) for p in found for f in pkg_sources[p]})
                violations.append(
                    self._violation(
                        file=self.root,
                        line=None,
                        message=(
                            f"conflicting packages - keep exactly one of "
                            f"{', '.join(found)} "
                            f"(found in: {', '.join(source_names)})"
                        ),
                    )
                )

        for pkg in banned:
            if pkg in pkg_sources:
                for dep_file in pkg_sources[pkg]:
                    violations.append(
                        self._violation(
                            file=dep_file,
                            line=None,
                            message=f"banned dependency '{pkg}'",
                        )
                    )

        return violations
