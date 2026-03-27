# Arklint

> The architectural rulebook for your codebase. Prevention, not detection.

[![PyPI version](https://badge.fury.io/py/arklint.svg)](https://pypi.org/project/arklint/)
[![npm version](https://badge.fury.io/js/arklint.svg)](https://www.npmjs.com/package/arklint)
[![NuGet version](https://badge.fury.io/nu/arklint.svg)](https://www.nuget.org/packages/arklint/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

Arklint enforces **architectural rules** before bad code ever lands — whether written by AI agents or humans. It's language-agnostic, runs locally with zero cloud dependency, and takes 60 seconds to set up.

```
$ arklint check

Arklint v0.5.1 — Scanning 142 files against 5 rules...

  ✗ FAIL  no-direct-db-in-routes
         API routes must not import database modules directly
         routes/users.py → imports 'sqlalchemy' — blocked by this rule
         routes/orders.py → imports 'psycopg2' — blocked by this rule

  ⚠ WARN  no-print-statements
         services/email.py:45 → banned pattern matched: 'print('

  ✓ PASS  models-in-models-dir
  ✓ PASS  layered-architecture

────────────────────────────────────────────────────────
Results: 1 error, 1 warning, 2 passed
────────────────────────────────────────────────────────
```

---

## Installation

Install whichever way fits your stack — they all run the same binary.

### Python
```bash
pip install arklint
```

### Node.js / JavaScript
```bash
# run once without installing
npx arklint check

# or install globally
npm install -g arklint
```

### .NET
```bash
dotnet tool install -g arklint
```

### Download binary directly

Grab the prebuilt binary for your platform from [GitHub Releases](https://github.com/Kaushik13k/arklint/releases/latest):

| Platform | Binary |
|---|---|
| Linux (x86_64) | `arklint-linux-x86_64` |
| macOS (Apple Silicon) | `arklint-darwin-arm64` |
| Windows (x86_64) | `arklint-windows-x86_64.exe` |

```bash
# macOS example
curl -L https://github.com/Kaushik13k/arklint/releases/latest/download/arklint-darwin-arm64 -o arklint
chmod +x arklint
# Note: first run on macOS may require: xattr -d com.apple.quarantine ./arklint
./arklint check
```

---

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

## Official rule packs

Arklint ships with ready-made rule packs for popular frameworks. Add one in seconds:

```bash
arklint search fastapi          # browse available packs
arklint add arklint/fastapi     # add to .arklint.yml
```

| Pack | Rules | Description |
|------|-------|-------------|
| `arklint/fastapi` | 4 | FastAPI service/route/schema separation |
| `arklint/django` | 4 | Django model/view/serializer placement |
| `arklint/nextjs` | 3 | Next.js server/client boundary rules |
| `arklint/express` | 3 | Express route/service separation |
| `arklint/clean-arch` | 2 | Clean architecture layer ordering |

Packs are composable — mix framework packs with your own project rules:

```yaml
# .arklint.yml
version: "1"
extends:
  - arklint/fastapi
  - arklint/clean-arch
rules:
  # your project-specific rules here
  - id: no-direct-db-in-routes
    type: boundary
    ...
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
arklint init                          Create a starter .arklint.yml
arklint init --force                  Overwrite existing config

arklint check                         Scan from current directory
arklint check ./src                   Scan a specific directory
arklint check --strict                Exit 1 on warnings too
arklint check --quiet / -q            Suppress passing rules
arklint check --json                  Machine-readable JSON output
arklint check --diff origin/main      Only scan files changed vs base
arklint check --github-annotations    Emit GitHub PR inline annotations
arklint check -c path/.arklint.yml    Use a specific config

arklint validate                      Validate config without checking
arklint validate -c path/.arklint.yml Validate a specific config file

arklint search <query>                Search official rule packs
arklint add arklint/<pack>            Add a pack to .arklint.yml

arklint export --format cursorrules   Export rules for Cursor IDE
arklint export --format claude        Export rules for Claude Code
arklint export --format copilot       Export rules for GitHub Copilot

arklint learn --describe <text>       Generate a rule from plain English
arklint learn --provider anthropic    AI provider (anthropic or openai)
arklint learn --append                Append rule without prompting

arklint visualize                     Print Mermaid diagram of rules
arklint visualize -o diagram.md       Write diagram to a file

arklint watch                         Re-run on every file save
arklint watch --strict                Watch mode with strict severity

arklint mcp                           Start MCP server for AI agents
arklint --version                     Show version and exit
```

---

## CI integration

### GitHub Action

```yaml
- uses: actions/checkout@v5
  with:
    fetch-depth: 0
- uses: Kaushik13k/arklint@v0.5.1
  with:
    strict: "true"          # exit 1 on warnings too
    diff: origin/main       # only scan changed files (fast)
```

### pip

```yaml
- name: Arklint
  run: |
    pip install arklint
    arklint check --diff origin/main --strict
```

### .NET projects

```yaml
- name: Arklint
  run: |
    dotnet tool install -g arklint
    arklint check --diff origin/main --strict
```

---

## pre-commit

```yaml
- repo: https://github.com/Kaushik13k/arklint
  rev: v0.5.1
  hooks:
    - id: arklint
```

---

## MCP server (AI agents)

Connect Claude, Cursor, or any MCP-compatible agent to arklint so it can query your architectural rules before generating code:

```bash
pip install 'arklint[mcp]'
arklint mcp
```

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "arklint": {
      "command": "arklint",
      "args": ["mcp"]
    }
  }
}
```

Tools exposed: `list_rules`, `get_rule_details`, `check_file`, `check_snippet`.

---

## Export rules for AI assistants

Keep your AI coding tools aligned with the same architectural constraints:

```bash
arklint export --format cursorrules   # → .cursorrules
arklint export --format claude        # → CLAUDE.md
arklint export --format copilot       # → .github/copilot-instructions.md
```

---

## Visualize your architecture

Generate a [Mermaid](https://mermaid.live) diagram of your layer dependencies and import boundaries:

```bash
arklint visualize
arklint visualize -o docs/architecture.md
```

---

## Supported languages

Import extraction works for: Python, JavaScript, TypeScript, Go, Ruby, Rust, Java, C#, PHP.

Dependency parsing works for: `requirements.txt`, `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile`.

---

## License

MIT — see [LICENSE](LICENSE).
