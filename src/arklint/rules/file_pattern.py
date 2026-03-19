"""File-pattern rule — ensure code patterns only appear in allowed directories.

Example config::

    - id: models-in-models-dir
      type: file-pattern
      description: "Data models must live in models/ or schemas/"
      pattern: 'class\\s+\\w*(Model|Schema)\\s*[:(]'
      allowed_in:
        - "models/**"
        - "schemas/**"
      severity: warning
"""
from __future__ import annotations

import re
from pathlib import Path

import pathspec

from .base import BaseRule, Violation
from arklint.parsers.patterns import scan_pattern


class FilePatternRule(BaseRule):
    """Report uses of *pattern* that appear outside the declared *allowed_in* paths."""

    def check(self, files: list[Path]) -> list[Violation]:
        raw = self.config.raw
        pattern: str = raw.get("pattern", "")
        allowed_globs: list[str] = (
            [raw["allowed_in"]]
            if isinstance(raw.get("allowed_in"), str)
            else raw.get("allowed_in", [])
        )

        if not pattern or not allowed_globs:
            return []

        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(
                f"Rule '{self.config.id}': invalid regex pattern {pattern!r}: {exc}"
            ) from exc

        allowed_spec = pathspec.PathSpec.from_lines("gitignore", allowed_globs)

        violations: list[Violation] = []
        for file in files:
            rel = self._rel(file)
            if allowed_spec.match_file(rel):
                continue  # file is in an allowed location — skip

            for match in scan_pattern(file, pattern):
                violations.append(
                    self._violation(
                        file=file,
                        line=match.line_number,
                        message=(
                            f"pattern {match.match!r} found outside allowed paths "
                            f"({', '.join(allowed_globs)})"
                        ),
                    )
                )

        return violations
