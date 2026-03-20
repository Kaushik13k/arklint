from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

import yaml

PACKS_CACHE_DIR = Path.home() / ".arklint" / "packs"
REGISTRY_URL = (
    "https://raw.githubusercontent.com/Kaushik13k/arklint/main/packs/registry.json"
)
PACK_BASE_URL = (
    "https://raw.githubusercontent.com/Kaushik13k/arklint/main/packs/{name}.yml"
)


class PackError(Exception):
    pass


def resolve_pack(ref: str, config_root: Path) -> list[dict[str, Any]]:
    """Resolve a pack reference and return its raw rules list.

    Supports:
      - Local path  : ./my-rules.yml  or  /abs/path.yml
      - Named pack  : arklint/fastapi
    """
    if ref.startswith("./") or ref.startswith("/") or ref.startswith("../"):
        return _load_local(ref, config_root)
    return _load_named(ref)


def fetch_registry() -> dict[str, Any]:
    """Fetch the official pack registry JSON."""
    try:
        with urllib.request.urlopen(REGISTRY_URL, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        raise PackError(f"Could not fetch registry: {exc}") from exc


def search_packs(query: str) -> list[dict[str, Any]]:
    """Search registry for packs matching query."""
    registry = fetch_registry()
    q = query.lower()
    return [
        p for p in registry.get("packs", [])
        if q in p.get("name", "").lower()
        or q in p.get("description", "").lower()
        or any(q in t.lower() for t in p.get("tags", []))
    ]


def list_all_packs() -> list[dict[str, Any]]:
    """Return all packs from the registry."""
    registry = fetch_registry()
    return registry.get("packs", [])


# ── private helpers ──────────────────────────────────────────────────────────

def _load_local(ref: str, config_root: Path) -> list[dict[str, Any]]:
    path = (config_root / ref).resolve()
    if not path.exists():
        raise PackError(f"Local pack not found: {path}")
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise PackError(f"Invalid YAML in pack {path}: {exc}") from exc
    return _extract_rules(data, ref)


def _load_named(name: str) -> list[dict[str, Any]]:
    cached = _cache_path(name)
    if cached.exists():
        try:
            data = yaml.safe_load(cached.read_text())
            return _extract_rules(data, name)
        except Exception:
            cached.unlink(missing_ok=True)

    url = PACK_BASE_URL.format(name=name.replace("/", "-").replace("arklint-", ""))
    # normalise: "arklint/fastapi" → fetch "fastapi.yml"
    pack_file = name.split("/")[-1]
    url = PACK_BASE_URL.format(name=pack_file)

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            content = resp.read().decode()
    except Exception as exc:
        raise PackError(
            f"Could not fetch pack '{name}'. "
            f"Run 'arklint search' to see available packs.\n{exc}"
        ) from exc

    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(content)

    data = yaml.safe_load(content)
    return _extract_rules(data, name)


def _extract_rules(data: Any, ref: str) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        raise PackError(f"Pack '{ref}' must be a YAML mapping")
    rules = data.get("rules", [])
    if not isinstance(rules, list):
        raise PackError(f"Pack '{ref}' 'rules' must be a list")
    return rules


def _cache_path(name: str) -> Path:
    safe = hashlib.md5(name.encode()).hexdigest()[:8] + "-" + name.replace("/", "-")
    return PACKS_CACHE_DIR / f"{safe}.yml"
