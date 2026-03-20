# arklint

> The architectural rulebook for your codebase. Prevention, not detection.

[![npm version](https://badge.fury.io/js/arklint.svg)](https://www.npmjs.com/package/arklint)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Kaushik13k/arklint/blob/main/LICENSE)

---

Arklint enforces **architectural rules** before bad code ever lands — whether written by AI agents or humans. It's language-agnostic, runs locally with zero cloud dependency, and takes 60 seconds to set up.

This package is a thin Node.js wrapper. On first run it downloads the platform-specific prebuilt binary from [GitHub Releases](https://github.com/Kaushik13k/arklint/releases) and caches it locally. **No Python required.**

Supported platforms: Linux x64, macOS ARM64 (Apple Silicon), Windows x64.

---

## Installation

```bash
# Run once without installing
npx arklint check

# Install globally
npm install -g arklint
```

---

## Quick start

```bash
# 1. Create a starter config in your project root
arklint init

# 2. Edit .arklint.yml to match your architecture

# 3. Check your codebase
arklint check

# 4. In CI — exit 1 on any violation
arklint check --strict
```

---

## Key commands

| Command | Description |
|---------|-------------|
| `arklint init` | Create a starter `.arklint.yml` |
| `arklint check` | Scan the codebase against all rules |
| `arklint check --strict` | Exit 1 on warnings too |
| `arklint check --diff origin/main` | Only scan changed files |
| `arklint check --json` | Machine-readable JSON output |
| `arklint check --github-annotations` | GitHub Actions inline PR annotations |
| `arklint validate` | Validate config without running checks |
| `arklint search <query>` | Search official rule packs |
| `arklint add arklint/fastapi` | Add an official rule pack |
| `arklint visualize` | Generate a Mermaid diagram of your rules |
| `arklint export --format cursorrules` | Export rules for Cursor/Claude/Copilot |
| `arklint learn --provider anthropic` | AI-powered rule generation |
| `arklint watch` | Re-run checks on every file save |
| `arklint mcp` | Start MCP server for AI agent integration |

---

## Example `.arklint.yml`

```yaml
version: "1"

# Extend an official rule pack
extends:
  - arklint/fastapi

# Add your own project-specific rules
rules:
  - id: no-direct-db-in-routes
    type: boundary
    description: "Routes must not import the database layer directly"
    source: "routes/**"
    blocked_imports:
      - "sqlalchemy"
      - "psycopg2"
    severity: error

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

## Official rule packs

```bash
arklint search fastapi
arklint add arklint/fastapi
arklint add arklint/django
arklint add arklint/nextjs
arklint add arklint/express
arklint add arklint/clean-arch
```

---

## Full documentation

[https://arklint.elevane.org](https://https://arklint.elevane.org) · [GitHub](https://github.com/Kaushik13k/arklint) · [PyPI](https://pypi.org/project/arklint/)

---

## License

MIT © [Kaushik13k](https://github.com/Kaushik13k)
