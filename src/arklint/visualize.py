"""Generate a Mermaid diagram from the active arklint configuration.

Reads all rules from the loaded config and produces a diagram that shows:
- layer-boundary  → directed graph of allowed layer dependencies
- boundary        → which layers are blocked from which imports
- dependency      → which packages compete with each other

The output is a Mermaid ``flowchart LR`` block that can be pasted into any
Markdown file or rendered at mermaid.live.
"""
from __future__ import annotations

from arklint.config import ArklintConfig


def build_mermaid(cfg: ArklintConfig) -> str:
    """Return a Mermaid diagram string for *cfg*."""
    lines: list[str] = ["flowchart LR"]

    _add_layer_boundary(cfg, lines)
    _add_boundary(cfg, lines)
    _add_dependency(cfg, lines)

    if len(lines) == 1:
        lines.append("    %% no visualisable rules found")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Per rule-type renderers
# ---------------------------------------------------------------------------

def _add_layer_boundary(cfg: ArklintConfig, lines: list[str]) -> None:
    rules = [r for r in cfg.rules if r.type == "layer-boundary"]
    if not rules:
        return

    for rule in rules:
        raw = rule.raw
        layers: list[dict] = raw.get("layers", [])
        allowed: dict[str, list[str]] = raw.get("allowed_dependencies", {})

        if not layers:
            continue

        lines.append(
            f"\n    subgraph {_safe_id(rule.id)} [\"{rule.description}\"]")

        layer_names = [lay["name"] for lay in layers if lay.get("name")]

        # Node definitions with paths as labels
        for lay in layers:
            name = lay.get("name", "")
            path = lay.get("path", name)
            nid = _safe_id(name)
            lines.append(f"        {nid}[\"{name}\\n{path}\"]")

        # Edges - allowed deps get a solid arrow, blocked get a red X edge
        all_pairs: set[tuple[str, str]] = set()
        for src in layer_names:
            for tgt in layer_names:
                if src != tgt:
                    all_pairs.add((src, tgt))

        for src in layer_names:
            permitted: list[str] = allowed.get(src, [])
            for tgt in layer_names:
                if src == tgt:
                    continue
                src_id = _safe_id(src)
                tgt_id = _safe_id(tgt)
                if tgt in permitted:
                    lines.append(f"        {src_id} --> {tgt_id}")
                else:
                    lines.append(f"        {src_id} -. blocked .-> {tgt_id}")

        lines.append("    end")


def _add_boundary(cfg: ArklintConfig, lines: list[str]) -> None:
    rules = [r for r in cfg.rules if r.type == "boundary"]
    if not rules:
        return

    lines.append("\n    subgraph boundaries [\"Import boundaries\"]")
    for rule in rules:
        raw = rule.raw
        sources = raw.get("source", [])
        if isinstance(sources, str):
            sources = [sources]
        blocked: list[str] = raw.get("blocked_imports", [])

        for src in sources:
            src_id = _safe_id(f"src_{src}")
            lines.append(f"        {src_id}[\"{src}\"]")
            for pkg in blocked:
                pkg_id = _safe_id(f"pkg_{pkg}")
                lines.append(f"        {pkg_id}([\"{pkg}\"])")
                lines.append(f"        {src_id} -. blocked .-> {pkg_id}")

    lines.append("    end")


def _add_dependency(cfg: ArklintConfig, lines: list[str]) -> None:
    rules = [r for r in cfg.rules if r.type == "dependency"]
    if not rules:
        return

    lines.append("\n    subgraph deps [\"Dependency constraints\"]")
    for rule in rules:
        raw = rule.raw
        group: list[str] = raw.get("allow_only_one_of", [])
        if len(group) < 2:
            continue
        rule_id = _safe_id(rule.id)
        lines.append(f"        {rule_id}{{\"choose one\"}}")
        for pkg in group:
            pkg_id = _safe_id(f"dep_{pkg}")
            lines.append(f"        {pkg_id}([\"{pkg}\"])")
            lines.append(f"        {rule_id} --- {pkg_id}")

    lines.append("    end")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_id(text: str) -> str:
    """Convert an arbitrary string to a valid Mermaid node ID."""
    return (
        text.replace("/", "_")
            .replace("-", "_")
            .replace(".", "_")
            .replace("@", "_")
            .replace(" ", "_")
            .replace("\\", "_")
            .strip("_")
    )
