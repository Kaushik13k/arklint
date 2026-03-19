from __future__ import annotations

from pathlib import Path

import pathspec


DEFAULT_EXCLUDES = [
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    "*.egg-info",
    "dist",
    "build",
    ".tox",
]


def collect_files(root: Path) -> list[Path]:
    """Walk root, respecting .gitignore, and return all non-excluded files."""
    gitignore_spec = _load_gitignore(root)
    default_spec = pathspec.PathSpec.from_lines("gitignore", DEFAULT_EXCLUDES)

    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        rel_str = str(rel)
        if default_spec.match_file(rel_str):
            continue
        if gitignore_spec and gitignore_spec.match_file(rel_str):
            continue
        files.append(path)

    return files


def _load_gitignore(root: Path) -> pathspec.PathSpec | None:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return None
    lines = gitignore.read_text().splitlines()
    return pathspec.PathSpec.from_lines("gitignore", lines)
