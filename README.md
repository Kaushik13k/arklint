# Arklint

> The architectural rulebook for your codebase. Prevention, not detection.

[![PyPI version](https://badge.fury.io/py/arklint.svg)](https://pypi.org/project/arklint/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

---

Arklint enforces **architectural rules** before bad code ever lands — whether written by AI agents or humans. It's language-agnostic, runs locally with zero cloud dependency, and takes 60 seconds to set up.

```
$ arklint check

Arklint v0.1.1 — Scanning 142 files against 5 rules...

  ✗ FAIL  no-direct-db-in-routes
         API routes must not import database modules directly
         routes/users.py → imports 'sqlalchemy' — blocked by this rule
         routes/orders.py → imports 'psycopg2' — blocked by this rule

  ✗ FAIL  single-http-client
         conflicting packages — keep exactly one of requests, httpx

  ⚠ WARN  no-print-statements
         services/email.py:45 → banned pattern matched: 'print('

  ✓ PASS  models-in-models-dir
  ✓ PASS  layered-architecture

────────────────────────────────────────────────────────
Results: 2 errors, 1 warning, 2 passed
────────────────────────────────────────────────────────
```

---

## Installation

```bash
pip install arklint
```

## Quick start

```bash
# 1. Generate a starter config
arklint init

# 2. Edit .arklint.yml to match your architecture (takes 2 minutes)

# 3. Run a check
arklint check

# 4. Add to pre-commit or CI
arklint check --strict   # exits 1 on warnings too
```

---

## Rule types

### `boundary` — Import restrictions between directories

Prevent files in source directories from importing blocked packages.

```yaml
- id: no-direct-db-in-routes
  type: boundary
  description: "API routes must not import the database layer directly"
  source: "routes/**"
  blocked_imports:
    - "sqlalchemy"
    - "psycopg2"
    - "pymongo"
  severity: error
```

### `dependency` — Control what packages are in the project

Detect conflicting or banned dependencies in `requirements.txt`, `package.json`, `go.mod`, and more.

```yaml
- id: single-http-client
  type: dependency
  description: "Pick one HTTP client and stick with it"
  allow_only_one_of:
    - "requests"
    - "httpx"
    - "aiohttp"
  severity: error
```

### `file-pattern` — Code patterns only allowed in specific directories

```yaml
- id: models-in-models-dir
  type: file-pattern
  description: "Data models must live in models/ or schemas/"
  pattern: 'class\s+\w*(Model|Schema)\s*[:(]'
  allowed_in:
    - "models/**"
    - "schemas/**"
  severity: warning
```

### `pattern-ban` — Ban a pattern across the codebase

```yaml
- id: no-print-statements
  type: pattern-ban
  description: "Use structured logging, not print()"
  pattern: 'print\('
  exclude:
    - "tests/**"
    - "scripts/**"
  severity: warning
```

### `layer-boundary` — Enforce layered architecture

Control which layers are allowed to import from which.

```yaml
- id: layered-architecture
  type: layer-boundary
  description: "Enforce routes → services → repositories"
  layers:
    - name: routes
      path: "routes/**"
    - name: services
      path: "services/**"
    - name: repositories
      path: "repositories/**"
  allowed_dependencies:
    routes: [services]
    services: [repositories]
    repositories: []
  severity: error
```

---

## CLI reference

```
arklint init              Create a starter .arklint.yml
arklint init --force      Overwrite existing config

arklint check             Scan from current directory
arklint check ./src       Scan a specific directory
arklint check --strict    Exit 1 on warnings too
arklint check --json      Machine-readable JSON output
arklint check -c path/to/.arklint.yml   Use a specific config
```

## CI integration

```yaml
# GitHub Actions
- name: Arklint
  run: |
    pip install arklint
    arklint check --strict
```

## pre-commit

```yaml
- repo: https://github.com/Kaushik13k/ark-lint
  rev: v0.1.0
  hooks:
    - id: arklint
```

---

## Supported languages

Import extraction works for: Python, JavaScript, TypeScript, Go, Ruby, Rust, Java, C#, PHP.

Dependency parsing works for: `requirements.txt`, `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile`.

---

## License

MIT — see [LICENSE](LICENSE).
