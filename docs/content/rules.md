# Rule Types

Arklint ships with five rule types. Each targets a specific class of architectural violation. All are language-agnostic and configured in `.arklint.yml`.

## boundary — Import Restrictions

Block files in a source directory from importing specific packages. Keep API routes away from raw database drivers.

```yaml
- id: no-direct-db-in-routes
  type: boundary
  source: "routes/**"
  blocked_imports:
    - "sqlalchemy"
    - "psycopg2"
    - "pymongo"
  severity: error
```

## dependency — Package Conflicts

Detect when multiple libraries serving the same purpose exist in your dependency file.

```yaml
- id: single-http-client
  type: dependency
  allow_only_one_of:
    - "requests"
    - "httpx"
    - "aiohttp"
  severity: error
```

## file-pattern — Code Placement

Ensure certain code patterns only exist in the right directories.

```yaml
- id: models-in-models-dir
  type: file-pattern
  pattern: 'class\s+\w*Model'
  allowed_in:
    - "models/**"
    - "schemas/**"
  severity: warning
```

## pattern-ban — Banned Patterns

Ban any regex pattern across the codebase with optional directory exclusions.

```yaml
- id: no-print-statements
  type: pattern-ban
  pattern: '(?<!\.)print\('
  exclude:
    - "tests/**"
    - "scripts/**"
  severity: warning
```

## layer-boundary — Layered Architecture

Define layers and control which ones can import from which. Enforce strict dependency direction.

```yaml
- id: layered-architecture
  type: layer-boundary
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
