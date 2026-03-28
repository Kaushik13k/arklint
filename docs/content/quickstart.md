# Quick Start

Get from install to your first architecture check in four steps.

## 1. Generate a starter config

Run `arklint init` in your project root. Arklint detects your ecosystem (Python, Node.js, or .NET) and generates a `.arklint.yml` with sensible starter rules for that stack.

```bash
$ cd ~/my-project
$ arklint init
```

## 2. Edit your rules

Open `.arklint.yml` and tailor the rules to your architecture - import boundaries, banned patterns, layered dependencies - all in readable YAML.

```yaml
version: "1"

rules:
  - id: no-direct-db-in-routes
    type: boundary
    description: "API routes must not import database modules"
    source: "routes/**"
    blocked_imports:
      - "sqlalchemy"
      - "psycopg2"
    severity: error

  - id: no-print-statements
    type: pattern-ban
    pattern: 'print\('
    exclude:
      - "tests/**"
    severity: warning
```

## 3. Run the check

Scan your codebase. Add flags as needed:

```bash
$ arklint check
$ arklint check --strict       # exit 1 on warnings too
$ arklint check --json         # JSON output for CI
$ arklint check --diff main    # only scan changed files
```

## 4. Add to your workflow

- **Watch mode** - instant feedback as you code: `arklint watch`
- **Pre-commit hook** - block violations before they're committed
- **CI gate** - fail the pipeline on violations
- **GitHub Action** - first-class Action with diff mode and version pinning

See [CI / Pre-commit](#ci) and [GitHub Action](#action) for ready-to-copy configs.
