from __future__ import annotations

import subprocess
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
    ".arklint.yml",
    ".arklint.yaml",
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


def collect_diff_files(root: Path, base: str = "HEAD") -> list[Path]:
    """Return only files that differ from *base* (git-aware).

    Runs ``git diff --name-only <base>`` plus ``git diff --name-only`` (staged)
    so both staged and unstaged changes are included.
    """
    def _git(*args: str) -> list[str]:
        try:
            result = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True,
                text=True,
                check=True,
            )
            return [l for l in result.stdout.splitlines() if l.strip()]
        except subprocess.CalledProcessError:
            return []

    names: set[str] = set()
    # committed changes vs base
    names.update(_git("diff", "--name-only", base))
    # staged (index vs HEAD)
    names.update(_git("diff", "--name-only", "--cached"))
    # unstaged (working tree vs index)
    names.update(_git("diff", "--name-only"))

    gitignore_spec = _load_gitignore(root)
    default_spec = pathspec.PathSpec.from_lines("gitignore", DEFAULT_EXCLUDES)

    files = []
    for name in sorted(names):
        path = (root / name).resolve()
        if not path.is_file():
            continue
        try:
            rel_str = str(path.relative_to(root))
        except ValueError:
            continue
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
