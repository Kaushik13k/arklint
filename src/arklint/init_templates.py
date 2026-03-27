"""Starter .arklint.yml templates emitted by `arklint init`.

A template is chosen based on markers found in the current directory:
  - package.json           → Node / TypeScript
  - *.csproj / *.sln       → .NET / C#
  - pyproject.toml etc.    → Python
  - (none matched)         → generic fallback
"""
from __future__ import annotations

from pathlib import Path


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

_PYTHON_TEMPLATE = r"""version: "1"

# Arklint — architectural rules for your Python project
# Docs: https://arklintapp.com

rules:
  # ── BOUNDARY ──────────────────────────────────────────────────────────────
  # API routes must never touch the database directly.
  - id: no-direct-db-in-routes
    type: boundary
    description: "API routes must not import database modules directly"
    source: "routes/**"
    blocked_imports:
      - "sqlalchemy"
      - "psycopg2"
      - "pymongo"
    severity: error

  # ── DEPENDENCY ────────────────────────────────────────────────────────────
  # Pick one HTTP client and stick with it.
  - id: single-http-client
    type: dependency
    description: "Only one HTTP client library allowed"
    allow_only_one_of:
      - "requests"
      - "httpx"
      - "aiohttp"
    severity: error

  # ── FILE-PATTERN ──────────────────────────────────────────────────────────
  # Data models belong in models/ or schemas/ — nowhere else.
  - id: models-in-models-dir
    type: file-pattern
    description: "Data models must live in models/ or schemas/"
    pattern: 'class\s+\w*(Model|Schema)\s*[:(]'
    allowed_in:
      - "models/**"
      - "schemas/**"
    severity: warning

  # ── PATTERN-BAN ───────────────────────────────────────────────────────────
  # Use structured logging — never bare print().
  - id: no-print-statements
    type: pattern-ban
    description: "Use structured logging, not print()"
    pattern: 'print\('
    exclude:
      - "tests/**"
      - "scripts/**"
    severity: warning

  # ── LAYER-BOUNDARY ────────────────────────────────────────────────────────
  # Enforce a strict dependency direction: routes → services → repositories.
  - id: layered-architecture
    type: layer-boundary
    description: "Enforce routes → services → repositories dependency direction"
    layers:
      - name: routes
        path: "routes/**"
      - name: services
        path: "services/**"
      - name: repositories
        path: "repositories/**"
    allowed_dependencies:
      routes:
        - services
      services:
        - repositories
      repositories: []
    severity: error
"""

_NODE_TEMPLATE = r"""version: "1"

# Arklint — architectural rules for your Node / TypeScript project
# Docs: https://arklintapp.com

rules:
  # ── BOUNDARY ──────────────────────────────────────────────────────────────
  # Route handlers must not reach into the database directly.
  - id: no-direct-db-in-routes
    type: boundary
    description: "Route handlers must not import database modules directly"
    source: "routes/**"
    blocked_imports:
      - "prisma"
      - "mongoose"
      - "pg"
      - "mysql2"
    severity: error

  # ── DEPENDENCY ────────────────────────────────────────────────────────────
  # Pick one HTTP client and stick with it.
  - id: single-http-client
    type: dependency
    description: "Only one HTTP client library allowed"
    allow_only_one_of:
      - "axios"
      - "node-fetch"
      - "got"
      - "ky"
    severity: error

  # ── FILE-PATTERN ──────────────────────────────────────────────────────────
  # Type definitions belong in types/ or models/ — not scattered around.
  - id: types-in-types-dir
    type: file-pattern
    description: "Shared types must live in types/ or models/"
    pattern: 'export\s+(interface|type)\s+\w+'
    allowed_in:
      - "types/**"
      - "models/**"
      - "src/types/**"
      - "src/models/**"
    severity: warning

  # ── PATTERN-BAN ───────────────────────────────────────────────────────────
  # Use a logger — never raw console.log in production code.
  - id: no-console-log
    type: pattern-ban
    description: "Use a structured logger, not console.log"
    pattern: 'console\.log\('
    exclude:
      - "**/*.test.ts"
      - "**/*.spec.ts"
      - "scripts/**"
    severity: warning

  # ── LAYER-BOUNDARY ────────────────────────────────────────────────────────
  # Enforce a strict dependency direction: routes → services → repositories.
  - id: layered-architecture
    type: layer-boundary
    description: "Enforce routes → services → repositories dependency direction"
    layers:
      - name: routes
        path: "routes/**"
      - name: services
        path: "services/**"
      - name: repositories
        path: "repositories/**"
    allowed_dependencies:
      routes:
        - services
      services:
        - repositories
      repositories: []
    severity: error
"""

_DOTNET_TEMPLATE = r"""version: "1"

# Arklint — architectural rules for your .NET / C# project
# Docs: https://arklintapp.com

rules:
  # ── BOUNDARY ──────────────────────────────────────────────────────────────
  # Controllers must not access the database directly — use repositories.
  - id: no-direct-db-in-controllers
    type: boundary
    description: "Controllers must not reference DbContext or raw SQL directly"
    source: "Controllers/**"
    blocked_imports:
      - "Microsoft.EntityFrameworkCore"
      - "System.Data.SqlClient"
      - "Dapper"
    severity: error

  # ── DEPENDENCY ────────────────────────────────────────────────────────────
  # Pick one serialisation library and stick with it.
  - id: single-json-library
    type: dependency
    description: "Only one JSON library allowed"
    allow_only_one_of:
      - "Newtonsoft.Json"
      - "System.Text.Json"
    severity: error

  # ── FILE-PATTERN ──────────────────────────────────────────────────────────
  # DTOs belong in Models/ or DTOs/ — not inside Controllers or Services.
  - id: dtos-in-models-dir
    type: file-pattern
    description: "DTO / model classes must live in Models/ or DTOs/"
    pattern: 'public\s+(class|record)\s+\w+(Dto|Request|Response|Model)\b'
    allowed_in:
      - "Models/**"
      - "DTOs/**"
      - "Contracts/**"
    severity: warning

  # ── PATTERN-BAN ───────────────────────────────────────────────────────────
  # Use ILogger — never raw Console.WriteLine in production code.
  - id: no-console-writeline
    type: pattern-ban
    description: "Use ILogger, not Console.WriteLine"
    pattern: 'Console\.Write(Line)?\('
    exclude:
      - "**/*Tests/**"
      - "scripts/**"
    severity: warning

  # ── LAYER-BOUNDARY ────────────────────────────────────────────────────────
  # Enforce strict Clean Architecture direction.
  - id: clean-architecture
    type: layer-boundary
    description: "Enforce Controllers → Services → Repositories direction"
    layers:
      - name: controllers
        path: "Controllers/**"
      - name: services
        path: "Services/**"
      - name: repositories
        path: "Repositories/**"
    allowed_dependencies:
      controllers:
        - services
      services:
        - repositories
      repositories: []
    severity: error
"""

# Generic fallback (original template)
STARTER_TEMPLATE = _PYTHON_TEMPLATE


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def detect_template(directory: Path) -> tuple[str, str]:
    """Return (template_content, ecosystem_label) for *directory*."""
    files = {p.name for p in directory.iterdir() if p.is_file()}
    csproj = any(p.suffix in (".csproj", ".sln") for p in directory.iterdir() if p.is_file())

    if "package.json" in files:
        return _NODE_TEMPLATE, "Node / TypeScript"
    if csproj:
        return _DOTNET_TEMPLATE, ".NET / C#"
    if files & {"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile"}:
        return _PYTHON_TEMPLATE, "Python"
    return _PYTHON_TEMPLATE, "Python"
