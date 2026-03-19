from __future__ import annotations

import json
import re
from pathlib import Path


_REQUIREMENTS_RE = re.compile(r"^\s*([A-Za-z0-9_\-\.]+)", re.MULTILINE)
_TOML_DEP_RE = re.compile(r"""^\s*["']?([A-Za-z0-9_\-\.]+)["']?\s*[=<>!~]""", re.MULTILINE)


def parse_dependency_file(path: Path) -> list[str]:
    """Return a list of package names from a dependency file."""
    name = path.name.lower()

    try:
        content = path.read_text(errors="ignore")
    except OSError:
        return []

    if name in ("requirements.txt", "requirements-dev.txt", "requirements-test.txt"):
        return _parse_requirements(content)

    if name == "package.json":
        return _parse_package_json(content)

    if name in ("pyproject.toml", "cargo.toml"):
        return _parse_toml_deps(content)

    if name == "go.mod":
        return _parse_go_mod(content)

    if name == "gemfile":
        return _parse_gemfile(content)

    return []


def _parse_requirements(content: str) -> list[str]:
    packages = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        m = re.match(r"([A-Za-z0-9_\-\.]+)", line)
        if m:
            packages.append(m.group(1).lower())
    return packages


def _parse_package_json(content: str) -> list[str]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []
    packages = []
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        packages.extend(data.get(section, {}).keys())
    return [p.lower() for p in packages]


def _parse_toml_deps(content: str) -> list[str]:
    # Simple extraction: find lines like package = "version" under [dependencies]
    in_deps = False
    packages = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and "dependencies" in stripped.lower():
            in_deps = True
            continue
        if stripped.startswith("[") and in_deps:
            in_deps = False
        if in_deps:
            m = re.match(r"""([A-Za-z0-9_\-\.]+)\s*[=]""", stripped)
            if m:
                packages.append(m.group(1).lower())
    return packages


def _parse_go_mod(content: str) -> list[str]:
    packages = []
    in_require = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "require (":
            in_require = True
            continue
        if stripped == ")" and in_require:
            in_require = False
            continue
        if stripped.startswith("require "):
            # single-line: require github.com/foo/bar v1.0
            parts = stripped.split()
            if len(parts) >= 2:
                packages.append(parts[1].lower())
        elif in_require:
            parts = stripped.split()
            if parts:
                packages.append(parts[0].lower())
    return packages


def _parse_gemfile(content: str) -> list[str]:
    packages = []
    for m in re.finditer(r"""gem\s+['"]([^'"]+)['"]""", content):
        packages.append(m.group(1).lower())
    return packages
