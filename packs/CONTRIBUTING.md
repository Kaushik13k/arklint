# Contributing Rule Packs

Rule packs are shareable bundles of arklint rules for a specific framework, architecture pattern, or language convention. They live in `packs/` and are fetched automatically when a user runs `arklint add arklint/<name>`.

Contributing a pack is the easiest way to contribute to arklint — **no Python required, just YAML.**

---

## What makes a good pack

- **Focused** — one framework or pattern per pack (e.g. `fastapi`, not `python-everything`)
- **Opinionated but safe** — rules should reflect widely-accepted best practices, not personal style
- **Severity-appropriate** — use `error` only for things that will definitely break or cause security issues; use `warning` for things that are bad practice but not catastrophic
- **Well-scoped** — avoid rules that fire on files they're not meant to check (use `exclude` and `source` carefully)
- **Tested mentally** — before submitting, ask: "would this fire on a clean, well-structured project?"

---

## Pack file format

```yaml
name: arklint/<your-pack-name>
description: One-line summary of what this pack enforces.
version: "1"

rules:
  - id: <pack-name>/<rule-id>        # e.g. flask/no-direct-db-in-routes
    type: <rule-type>                 # boundary | dependency | file-pattern | pattern-ban | layer-boundary
    description: What this rule enforces and why.
    # ... rule-type-specific fields (see below)
    severity: error | warning
```

### Rule type field reference

**pattern-ban**
```yaml
- id: mypack/no-print
  type: pattern-ban
  description: No print() in production code.
  pattern: 'print\('
  exclude: ["tests/**", "scripts/**"]   # optional
  severity: warning
```

**boundary**
```yaml
- id: mypack/no-db-in-routes
  type: boundary
  description: Routes must not import DB drivers directly.
  source: "routes/**"                   # glob or list of globs
  blocked_imports: ["sqlalchemy", "pg"]
  severity: error
```

**file-pattern**
```yaml
- id: mypack/models-in-models-dir
  type: file-pattern
  description: Models must live in models/ directory.
  pattern: 'class\s+\w+\s*\(\s*Base\s*\)'
  allowed_in: ["models/**", "**/models.py"]
  severity: warning
```

**dependency**
```yaml
- id: mypack/single-http-client
  type: dependency
  description: Use only one HTTP client.
  allow_only_one_of: ["httpx", "requests", "aiohttp"]
  severity: warning
```

**layer-boundary**
```yaml
- id: mypack/clean-layers
  type: layer-boundary
  description: Enforce clean architecture layer ordering.
  layers:
    - name: routes
      path: "routes/**"
    - name: services
      path: "services/**"
  allowed_dependencies:
    routes: [services]
    services: []
  severity: error
```

---

## Step-by-step: submitting a new pack

### 1. Create your pack file

```bash
cp packs/fastapi.yml packs/<your-pack>.yml
```

Edit it — use the format above. Name convention:
- File: `packs/<framework>.yml` (e.g. `packs/flask.yml`)
- Pack name: `arklint/<framework>` (e.g. `arklint/flask`)
- Rule IDs: `<framework>/<rule-slug>` (e.g. `flask/no-direct-db-in-views`)

### 2. Register it in registry.json

Add an entry to `packs/registry.json`:

```json
{
  "name": "arklint/<your-pack>",
  "description": "One-line description.",
  "tags": ["python", "flask", "web"],
  "rules": 3
}
```

Update `"rules"` to match the number of rules in your pack.

### 3. Test it locally

```bash
# Point a local .arklint.yml at your pack file
extends:
  - ./packs/<your-pack>.yml

# Then run
arklint validate
arklint check
```

### 4. Open a pull request

- Branch name: `pack/<framework>` (e.g. `pack/flask`)
- PR title: `pack: add arklint/<framework> rule pack`
- No Python tests required for pack-only changes
- Fill in the PR description template as usual

---

## Quality checklist (before submitting)

- [ ] Pack file is valid YAML (`arklint validate` passes)
- [ ] All rule IDs are prefixed with the pack name (e.g. `flask/...`)
- [ ] `description` is written in plain English and explains *why* the rule exists
- [ ] `severity: error` is only used for things that break or create security issues
- [ ] `exclude` paths are set where needed to avoid false positives on tests/scripts
- [ ] Pack name and rule count added to `packs/registry.json`
- [ ] `arklint check` still passes on the arklint repo itself

---

## Existing packs (reference implementations)

| Pack | File | Rules |
|---|---|---|
| `arklint/fastapi` | [fastapi.yml](fastapi.yml) | 4 |
| `arklint/django` | [django.yml](django.yml) | 4 |
| `arklint/nextjs` | [nextjs.yml](nextjs.yml) | 3 |
| `arklint/express` | [express.yml](express.yml) | 3 |
| `arklint/clean-arch` | [clean-arch.yml](clean-arch.yml) | 2 |

---

## Ideas for new packs

Looking for something to contribute? These are wanted:

- `arklint/flask` — Flask blueprint/model/service separation
- `arklint/sqlalchemy` — model placement, session management
- `arklint/celery` — task placement, no DB in tasks
- `arklint/nestjs` — NestJS module/service/controller separation
- `arklint/rails` — Rails MVC conventions
- `arklint/gin` — Go Gin handler/service/repository layers
- `arklint/microservices` — service boundary rules

---

## Questions?

Open an issue or start a discussion at [github.com/Kaushik13k/arklint](https://github.com/Kaushik13k/arklint).
