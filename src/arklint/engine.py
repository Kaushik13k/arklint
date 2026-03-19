"""Rule evaluation engine.

Orchestrates running every configured rule against the collected file list and
returns a structured result for each rule.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from arklint.config import ArklintConfig, RuleConfig
from arklint.rules import RULE_REGISTRY
from arklint.rules.base import Violation


@dataclass(slots=True)
class CheckResult:
    """The outcome of evaluating a single rule."""

    rule: RuleConfig
    violations: list[Violation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.violations

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")


def run_rules(
    config: ArklintConfig,
    files: list[Path],
    scan_root: Path | None = None,
) -> list[CheckResult]:
    """Evaluate every rule in *config* against *files*.

    *scan_root* overrides ``config.root`` when computing relative paths — use
    this when scanning a directory other than where ``.arklint.yml`` lives.

    Returns one :class:`CheckResult` per configured rule, in config order.
    """
    root = (scan_root or config.root).resolve()
    results: list[CheckResult] = []

    for rule_config in config.rules:
        rule_class = RULE_REGISTRY.get(rule_config.type)
        if rule_class is None:
            # Validated at load time; skip silently here.
            continue

        rule_instance = rule_class(rule_config, root)
        violations = rule_instance.check(files)
        results.append(CheckResult(rule=rule_config, violations=violations))

    return results
