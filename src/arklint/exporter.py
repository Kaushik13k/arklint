"""Export arklint rules as AI assistant instruction files.

Supported formats
-----------------
cursorrules  →  .cursorrules           (Cursor IDE)
claude       →  CLAUDE.md              (Claude Code)
copilot      →  .github/copilot-instructions.md  (GitHub Copilot)
"""
from __future__ import annotations

from pathlib import Path

from arklint.config import ArklintConfig, RuleConfig

SUPPORTED_FORMATS = ("cursorrules", "claude", "copilot")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export(cfg: ArklintConfig, fmt: str, output_dir: Path) -> Path:
    """Render *cfg* rules into the file for *fmt* inside *output_dir*.

    Returns the path of the written file.
    """
    content = _render(cfg, fmt)
    dest = _dest_path(output_dir, fmt)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _render(cfg: ArklintConfig, fmt: str) -> str:
    rules = cfg.rules
    if fmt == "cursorrules":
        return _render_cursorrules(rules)
    if fmt == "claude":
        return _render_claude(rules)
    if fmt == "copilot":
        return _render_copilot(rules)
    raise ValueError(f"Unknown export format: {fmt!r}")


def _rule_lines(rules: list[RuleConfig]) -> list[str]:
    """Return one bullet per rule: '- [severity] id: description'."""
    lines = []
    for r in rules:
        severity_tag = "ERROR" if r.severity == "error" else "WARN"
        desc = r.description or r.id
        lines.append(f"- [{severity_tag}] **{r.id}**: {desc}")
    return lines


def _render_cursorrules(rules: list[RuleConfig]) -> str:
    bullet_block = "\n".join(_rule_lines(rules))
    return (
        "# Arklint architectural rules\n"
        "# Auto-generated - do not edit by hand. Re-run `arklint export --format cursorrules`.\n\n"
        "## Code rules\n\n"
        "The following architectural rules are enforced by arklint. "
        "When writing or suggesting code, do not introduce violations:\n\n"
        f"{bullet_block}\n"
    )


def _render_claude(rules: list[RuleConfig]) -> str:
    bullet_block = "\n".join(_rule_lines(rules))
    return (
        "# Arklint architectural rules\n\n"
        "> Auto-generated - do not edit by hand. "
        "Re-run `arklint export --format claude` to refresh.\n\n"
        "## Rules\n\n"
        "The following architectural rules are enforced by arklint. "
        "When writing or suggesting code, do not introduce violations:\n\n"
        f"{bullet_block}\n"
    )


def _render_copilot(rules: list[RuleConfig]) -> str:
    bullet_block = "\n".join(_rule_lines(rules))
    return (
        "# Arklint architectural rules\n\n"
        "<!-- Auto-generated - do not edit by hand. "
        "Re-run `arklint export --format copilot` to refresh. -->\n\n"
        "## Code rules\n\n"
        "The following architectural rules are enforced by arklint. "
        "When writing or suggesting code, do not introduce violations:\n\n"
        f"{bullet_block}\n"
    )


# ---------------------------------------------------------------------------
# Destination paths
# ---------------------------------------------------------------------------

def _dest_path(output_dir: Path, fmt: str) -> Path:
    if fmt == "cursorrules":
        return output_dir / ".cursorrules"
    if fmt == "claude":
        return output_dir / "CLAUDE.md"
    if fmt == "copilot":
        return output_dir / ".github" / "copilot-instructions.md"
    raise ValueError(f"Unknown export format: {fmt!r}")
