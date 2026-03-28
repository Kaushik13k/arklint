"""Language-aware import extraction.

Each language extractor returns a list of *top-level package/module names*
(e.g. ``sqlalchemy``, not ``sqlalchemy.orm``). Normalization to lower-case and
deduplication are the caller's responsibility.

Supported languages (detected by file extension):
  .py          Python
  .js .ts .jsx .tsx .mjs .cjs   JavaScript / TypeScript
  .go          Go
  .rb          Ruby
  .rs          Rust
  .java        Java
  .cs          C#
  .php         PHP
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Per-language regex patterns
# ---------------------------------------------------------------------------

# Python ─────────────────────────────────────────────────────────────────────
# Matches:  import X          → group 1 = "X"
#           from X import ... → group 1 = "X"
_PY_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w., ]+))",
    re.MULTILINE,
)

# JavaScript / TypeScript ─────────────────────────────────────────────────────
# Matches:  import ... from 'X'   / import ... from "X"
#           require('X')          / require("X")
#           import('X')           / import("X")          (dynamic)
_JS_RE = re.compile(
    r"""(?:import\s[^'"]*?from\s|require\s*\(\s*|import\s*\(\s*)['"]([^'"]+)['"]""",
    re.MULTILINE,
)

# Go ──────────────────────────────────────────────────────────────────────────
# Only matches inside  import "..." or import ( ... ) blocks, never bare strings.
_GO_SINGLE_RE = re.compile(r'^\s*import\s+"([^"]+)"', re.MULTILINE)
_GO_BLOCK_RE = re.compile(r"import\s*\(([^)]*)\)", re.DOTALL)
_GO_PKG_RE = re.compile(r'(?:_\s+|[\w]+\s+)?"([^"]+)"')  # optional alias

# Ruby ────────────────────────────────────────────────────────────────────────
_RUBY_RE = re.compile(r"""^\s*require(?:_relative)?\s+['"]([^'"]+)['"]""", re.MULTILINE)

# Rust ────────────────────────────────────────────────────────────────────────
# Matches:  use X::...;   extern crate X;
_RUST_RE = re.compile(r"^\s*(?:use\s+([\w:]+)|extern\s+crate\s+([\w]+))", re.MULTILINE)

# Java ────────────────────────────────────────────────────────────────────────
_JAVA_RE = re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+\*?)\s*;", re.MULTILINE)

# C# ──────────────────────────────────────────────────────────────────────────
_CS_RE = re.compile(r"^\s*using\s+([\w.]+)\s*;", re.MULTILINE)

# PHP ─────────────────────────────────────────────────────────────────────────
_PHP_RE = re.compile(
    r"""^\s*(?:use|require(?:_once)?|include(?:_once)?)\s+['"]?([\w\\/.]+)['"]?\s*;""",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_imports(path: Path) -> list[str]:
    """Return a deduplicated list of imported package/module names from *path*.

    The result contains *full dotted import paths* (not just top-level names)
    so that callers can decide how to match.  For example::

        import sqlalchemy.orm   →  ["sqlalchemy.orm"]
        from sqlalchemy import  →  ["sqlalchemy"]

    Returns an empty list on read errors or unrecognized extensions.
    """
    try:
        content = path.read_text(errors="ignore")
    except OSError:
        return []

    suffix = path.suffix.lower()

    if suffix == ".py":
        return _dedup(_extract_python(content))
    if suffix in {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}:
        return _dedup(_extract_js(content))
    if suffix == ".go":
        return _dedup(_extract_go(content))
    if suffix == ".rb":
        return _dedup(_extract_ruby(content))
    if suffix == ".rs":
        return _dedup(_extract_rust(content))
    if suffix == ".java":
        return _dedup(_extract_java(content))
    if suffix == ".cs":
        return _dedup(_extract_csharp(content))
    if suffix == ".php":
        return _dedup(_extract_php(content))

    return []


# ---------------------------------------------------------------------------
# Language extractors (private)
# ---------------------------------------------------------------------------


def _extract_python(src: str) -> list[str]:
    results: list[str] = []
    for m in _PY_RE.finditer(src):
        if m.group(1):
            # from X import Y  → X
            results.append(m.group(1))
        else:
            # import X, Y, Z  → [X, Y, Z]
            for part in m.group(2).split(","):
                name = part.strip().split(" as ")[0].strip()
                if name:
                    results.append(name)
    return results


def _extract_js(src: str) -> list[str]:
    return [m.group(1) for m in _JS_RE.finditer(src)]


def _extract_go(src: str) -> list[str]:
    results: list[str] = []

    # Single-line: import "pkg"
    for m in _GO_SINGLE_RE.finditer(src):
        results.append(m.group(1))

    # Block: import ( ... )
    for block_match in _GO_BLOCK_RE.finditer(src):
        block = block_match.group(1)
        for m in _GO_PKG_RE.finditer(block):
            results.append(m.group(1))

    return results


def _extract_ruby(src: str) -> list[str]:
    return [m.group(1) for m in _RUBY_RE.finditer(src)]


def _extract_rust(src: str) -> list[str]:
    results: list[str] = []
    for m in _RUST_RE.finditer(src):
        path = m.group(1) or m.group(2)
        if path:
            # use std::collections::HashMap → std
            results.append(path.split("::")[0])
    return results


def _extract_java(src: str) -> list[str]:
    return [m.group(1) for m in _JAVA_RE.finditer(src)]


def _extract_csharp(src: str) -> list[str]:
    return [m.group(1) for m in _CS_RE.finditer(src)]


def _extract_php(src: str) -> list[str]:
    return [m.group(1) for m in _PHP_RE.finditer(src)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
