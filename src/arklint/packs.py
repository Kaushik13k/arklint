from __future__ import annotations

import hashlib
import json
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

PACKS_CACHE_DIR = Path.home() / ".arklint" / "packs"

# Pinned to a stable tag so pack content cannot change without a release.
_PACK_REF = "main"  # updated to a release tag on each arklint release
REGISTRY_URL = (
    f"https://raw.githubusercontent.com/Kaushik13k/arklint/{_PACK_REF}/packs/registry.json"
)
PACK_BASE_URL = (
    f"https://raw.githubusercontent.com/Kaushik13k/arklint/{_PACK_REF}/packs/{{name}}.yml"
)


class PackError(Exception):
    """Raised when a pack cannot be resolved, fetched, or parsed."""


def resolve_pack(ref: str, config_root: Path) -> list[dict[str, Any]]:
    """Resolve a pack reference and return its raw rules list.

    Supports:
      - Local path  : ./my-rules.yml  or  /abs/path.yml  or  C:\\...
      - Named pack  : arklint/fastapi
    """
    if not isinstance(ref, str):
        raise PackError(f"Pack reference must be a string, got {type(ref).__name__}: {ref!r}")

    # Detect local paths: relative prefixes, absolute POSIX, or absolute Windows
    ref_path = Path(ref)
    is_local = ref.startswith("./") or ref.startswith("../") or ref_path.is_absolute()
    if is_local:
        return _load_local(ref, config_root)
    return _load_named(ref)


def _urlopen(url: str, timeout: int = 10):
    """Open a URL, falling back to an unverified SSL context on certificate errors.

    macOS Python installs sometimes lack system CA certificates. Rather than
    failing hard, we retry without verification so the tool keeps working.
    """
    try:
        return urllib.request.urlopen(url, timeout=timeout)
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" in str(exc) or "SSL" in str(exc).upper():
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return urllib.request.urlopen(url, timeout=timeout, context=ctx)
        raise


def fetch_registry() -> dict[str, Any]:
    """Fetch the official pack registry JSON."""
    try:
        with _urlopen(REGISTRY_URL, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
        raise PackError(f"Could not fetch registry: {exc}") from exc


def search_packs(query: str) -> list[dict[str, Any]]:
    """Search registry for packs matching query (name, description, or tags)."""
    registry = fetch_registry()
    q = query.lower()
    return [
        p
        for p in registry.get("packs", [])
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
    path = Path(ref) if Path(ref).is_absolute() else (config_root / ref).resolve()
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
        except PackError:
            cached.unlink(missing_ok=True)
        except (yaml.YAMLError, OSError):
            cached.unlink(missing_ok=True)

    pack_file = name.split("/")[-1]
    url = PACK_BASE_URL.format(name=pack_file)

    try:
        with _urlopen(url, timeout=10) as resp:
            content = resp.read().decode()
    except (urllib.error.URLError, OSError) as exc:
        raise PackError(
            f"Could not fetch pack '{name}'. Run 'arklint search' to see available packs.\n{exc}"
        ) from exc

    # Validate before writing to cache
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise PackError(f"Remote pack '{name}' returned invalid YAML: {exc}") from exc

    rules = _extract_rules(data, name)  # raises PackError if malformed

    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(content)

    return rules


def _extract_rules(data: Any, ref: str) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        raise PackError(f"Pack '{ref}' must be a YAML mapping")
    if "rules" not in data:
        raise PackError(f"Pack '{ref}' must define a 'rules' key")
    rules = data["rules"]
    if not isinstance(rules, list):
        raise PackError(f"Pack '{ref}' 'rules' must be a list")
    return rules


def _cache_path(name: str) -> Path:
    safe = hashlib.md5(name.encode()).hexdigest()[:8] + "-" + name.replace("/", "-")
    return PACKS_CACHE_DIR / f"{safe}.yml"
