from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


VALID_RULE_TYPES = {"boundary", "dependency", "file-pattern", "pattern-ban", "layer-boundary"}
VALID_SEVERITIES = {"error", "warning"}


@dataclass
class RuleConfig:
    id: str
    type: str
    description: str
    severity: str
    raw: dict[str, Any]


@dataclass
class ArklintConfig:
    version: str
    rules: list[RuleConfig] = field(default_factory=list)
    root: Path = field(default_factory=Path.cwd)


class ConfigError(Exception):
    pass


def load_config(path: Path | None = None) -> ArklintConfig:
    if path is None:
        path = _find_config()

    if not path.exists():
        raise ConfigError(f"No .arklint.yml found. Run 'arklint init' to create one.")

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}")

    if not isinstance(data, dict):
        raise ConfigError(f"{path} must be a YAML mapping")

    version = str(data.get("version", "1"))

    # ── resolve extends ───────────────────────────────────────────────────────
    from arklint.packs import PackError, resolve_pack  # local import avoids cycle

    extends = data.get("extends", [])
    if not isinstance(extends, list):
        raise ConfigError("'extends' must be a list of pack references")

    extended_rules: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for i, ref in enumerate(extends):
        if not isinstance(ref, str):
            raise ConfigError(
                f"'extends' entry #{i + 1} must be a string, got {type(ref).__name__}: {ref!r}"
            )
        try:
            pack_rules = resolve_pack(ref, path.parent)
        except PackError as exc:
            raise ConfigError(f"Failed to load pack '{ref}': {exc}") from exc
        for raw in pack_rules:
            if not isinstance(raw, dict):
                raise ConfigError(
                    f"Pack '{ref}' contains an invalid rule entry (expected a mapping)"
                )
            rule_id = raw.get("id", "")
            if not rule_id:
                raise ConfigError(f"Pack '{ref}' contains a rule missing the 'id' field")
            if rule_id not in seen_ids:
                extended_rules.append(raw)
                seen_ids.add(rule_id)

    # ── local rules (override extended rules with same id) ────────────────────
    raw_rules = data.get("rules", [])
    if not isinstance(raw_rules, list):
        raise ConfigError("'rules' must be a list")

    local_ids = {r.get("id") for r in raw_rules if isinstance(r, dict)}
    merged_raw = [r for r in extended_rules if r.get("id") not in local_ids] + raw_rules

    rules = []
    for i, raw in enumerate(merged_raw):
        rule = _parse_rule(raw, i)
        rules.append(rule)

    return ArklintConfig(version=version, rules=rules, root=path.parent)


def _parse_rule(raw: Any, index: int) -> RuleConfig:
    if not isinstance(raw, dict):
        raise ConfigError(f"Rule #{index + 1} must be a mapping, got {type(raw).__name__}")

    rule_id = raw.get("id")
    if not rule_id:
        raise ConfigError(f"Rule #{index + 1} missing required field 'id'")

    rule_type = raw.get("type")
    if not rule_type:
        raise ConfigError(f"Rule '{rule_id}' missing required field 'type'")
    if rule_type not in VALID_RULE_TYPES:
        raise ConfigError(
            f"Rule '{rule_id}' has unknown type '{rule_type}'. "
            f"Valid types: {', '.join(sorted(VALID_RULE_TYPES))}"
        )

    description = raw.get("description", "")
    severity = raw.get("severity", "error")
    if severity not in VALID_SEVERITIES:
        raise ConfigError(
            f"Rule '{rule_id}' has invalid severity '{severity}'. "
            f"Use 'error' or 'warning'."
        )

    return RuleConfig(id=rule_id, type=rule_type, description=description, severity=severity, raw=raw)


def _find_config() -> Path:
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / ".arklint.yml"
        if candidate.exists():
            return candidate
    return current / ".arklint.yml"
