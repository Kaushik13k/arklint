"""Boundary rule — prevent cross-directory import violations.

Example config::

    - id: no-direct-db-in-routes
      type: boundary
      description: "API routes must not import database modules directly"
      source: "routes/**"
      blocked_imports:
        - "sqlalchemy"
        - "psycopg2"
      severity: error
"""
from __future__ import annotations

from pathlib import Path

import pathspec

from .base import BaseRule, Violation
from arklint.parsers.imports import extract_imports


class BoundaryRule(BaseRule):
    """Prevent files matched by *source* globs from importing blocked packages."""

    def check(self, files: list[Path]) -> list[Violation]:
        raw = self.config.raw
        source_globs: list[str] = (
            [raw["source"]] if isinstance(raw.get("source"), str) else raw.get("source", [])
        )
        blocked: list[str] = [b.lower() for b in raw.get("blocked_imports", [])]

        if not source_globs or not blocked:
            return []

        source_spec = pathspec.PathSpec.from_lines("gitignore", source_globs)

        violations: list[Violation] = []
        for file in files:
            rel = self._rel(file)
            if not source_spec.match_file(rel):
                continue

            # Deduplicate: one violation per (file, blocked_package) — don't
            # emit the same violation for `import sqlalchemy` AND
            # `from sqlalchemy import Session` in the same file.
            seen_blocked: set[str] = set()
            for imp in extract_imports(file):
                imp_lower = imp.lower()
                for blocked_pkg in blocked:
                    if blocked_pkg in seen_blocked:
                        continue
                    if imp_lower == blocked_pkg or imp_lower.startswith(blocked_pkg + "."):
                        seen_blocked.add(blocked_pkg)
                        violations.append(
                            self._violation(
                                file=file,
                                line=None,
                                message=f"imports '{imp}' — blocked by this rule",
                            )
                        )

        return violations
