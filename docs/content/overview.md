# Overview

Your codebase has architectural rules. Nobody enforces them. Arklint does.

## The problem nobody talks about

You've seen this happen. A pull request lands where a route handler imports directly from the database. Or an AI agent generates three files - clean code, wrong layer. Or `requirements.txt` quietly grows to include both `requests` *and* `httpx` because nobody was watching.

Code review catches *some* of this. Linters check syntax and style. But there's nothing - until now - that enforces *structural intent*: which module can import which, which packages can coexist, which patterns belong in which directories.

Without enforcement, the architecture degrades. Rules exist only as comments in a wiki nobody reads.

## What Arklint does

You write your architectural rules in a plain YAML file. Arklint checks them against your entire codebase in seconds - and blocks violations in CI before they ever merge.

```yaml
version: "1"

rules:
  - id: no-direct-db-in-routes
    type: boundary
    description: "Route handlers must not import database drivers directly"
    source: "routes/**"
    blocked_imports:
      - "sqlalchemy"
      - "psycopg2"
    severity: error

  - id: single-http-client
    type: dependency
    description: "Use exactly one HTTP client library"
    allow_only_one_of:
      - "requests"
      - "httpx"
    severity: error
```

Run the check:

```bash
$ arklint check

  ✗ FAIL  no-direct-db-in-routes
         routes/users.py → imports 'sqlalchemy' - blocked
         routes/orders.py → imports 'psycopg2' - blocked

  ✗ FAIL  single-http-client
         conflicting packages detected - keep one of: requests, httpx

  ✓ PASS  models-in-models-dir
  ✓ PASS  layered-architecture

Results: 2 errors, 2 passed
```

Violations are errors. Errors fail the pipeline. The architecture stays clean.

## What it checks

Arklint ships with five rule types covering the most common architectural violations:

| Rule type | What it enforces |
|-----------|-----------------|
| `boundary` | Which directories can import which packages |
| `dependency` | Which libraries can coexist in your dependency file |
| `file-pattern` | Where specific code patterns are allowed to live |
| `pattern-ban` | Regex patterns that must never appear in the codebase |
| `layer-boundary` | The allowed import direction between architectural layers |

## Where it runs

**Locally** - `arklint check` while you build; `arklint watch` for live feedback on every save.

**Pre-commit** - block violations before they're committed.

**CI** - `arklint check --strict` fails the pipeline. `--diff origin/main` makes it fast on large repos by scanning only changed files.

**Inside AI coding tools** - the MCP server lets Claude Code, Cursor, and Copilot check code *before writing it*. The `export` command writes your rules into `.cursorrules` or `CLAUDE.md` so AI agents understand your architecture natively.

## Core concepts

| Concept | Description |
|---------|-------------|
| **Rule** | A single architectural constraint - one `type`, one `id`, one `severity` |
| **`.arklint.yml`** | The config file where all your rules live |
| **Pack** | A shareable bundle of rules for a framework (e.g. `arklint/fastapi`) |
| **Check** | `arklint check` - scans every file against every rule |
| **MCP server** | Exposes your rules to AI agents via the Model Context Protocol |

## Get started

**Python**
```bash
$ pip install arklint
$ arklint init
$ arklint check
```

**Node.js**
```bash
$ npm install -g arklint
$ arklint init
$ arklint check
```

**.NET**
```bash
$ dotnet tool install -g arklint
$ arklint init
$ arklint check
```
