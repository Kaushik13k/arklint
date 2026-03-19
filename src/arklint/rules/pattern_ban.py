"""Pattern-ban rule — forbid a regex pattern across the codebase.

Example config::

    - id: no-print-statements
      type: pattern-ban
      description: "Use structured logging, not print()"
      pattern: 'print\\('
      exclude:
        - "tests/**"
        - "scripts/**"
      severity: warning
"""
from __future__ import annotations

import re
from pathlib import Path

import pathspec

from .base import BaseRule, Violation
from arklint.parsers.patterns import scan_pattern


class PatternBanRule(BaseRule):
    """Report every line that matches *pattern* outside excluded directories."""

    def check(self, files: list[Path]) -> list[Violation]:
        raw = self.config.raw
        pattern: str = raw.get("pattern", "")
        excludes: list[str] = raw.get("exclude", [])

        if not pattern:
            return []

        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(
                f"Rule '{self.config.id}': invalid regex pattern {pattern!r}: {exc}"
            ) from exc

        exclude_spec = (
            pathspec.PathSpec.from_lines("gitignore", excludes) if excludes else None
        )

        violations: list[Violation] = []
        for file in files:
            rel = self._rel(file)
            if exclude_spec and exclude_spec.match_file(rel):
                continue

            for match in scan_pattern(file, pattern):
                violations.append(
                    self._violation(
                        file=file,
                        line=match.line_number,
                        message=f"banned pattern matched: {match.match!r}",
                    )
                )

        return violations
