# Rule Packs

Rule packs are shareable bundles of arklint rules for a specific framework or architecture pattern. Use them to get started in seconds without writing rules from scratch.

## Browsing packs

```bash
$ arklint search fastapi
$ arklint search django
$ arklint search clean
```

## Adding a pack

```bash
$ arklint add arklint/fastapi
Fetching pack 'arklint/fastapi'…
✓ Added arklint/fastapi (6 rules) to .arklint.yml
  Run arklint validate to confirm.
```

This appends the pack to the `extends` list in your `.arklint.yml`. Your own rules always take precedence - if you define a rule with the same `id` as a pack rule, yours wins.

## Official packs

### Framework packs

| Pack | Rules | Description |
|------|-------|-------------|
| `arklint/fastapi` | 6 | FastAPI routers/services/schemas, settings placement, layered architecture |
| `arklint/django` | 6 | Django model/view/serializer placement, Celery tasks, signals, no raw SQL |
| `arklint/flask` | 6 | Flask blueprints, service layer, config management, no debug in prod |
| `arklint/nextjs` | 5 | Next.js server/client boundary, API routes, no process.env in components |
| `arklint/express` | 5 | Express route/controller/service separation, middleware placement |
| `arklint/nestjs` | 6 | NestJS controller/service/repository separation, DI patterns, single ORM |
| `arklint/spring` | 6 | Spring Boot layer separation, constructor injection, DTO placement |

### Architecture packs

| Pack | Rules | Description |
|------|-------|-------------|
| `arklint/clean-arch` | 3 | Clean architecture layer ordering, no framework in entities or use cases |

### General packs

| Pack | Rules | Description |
|------|-------|-------------|
| `arklint/security` | 8 | Bans eval, shell injection, unsafe deserialization, innerHTML, SQL string concat |
| `arklint/code-hygiene` | 5 | Bans TODO comments, debug breakpoints, sleep in tests, scattered test files |

## Using extends manually

```yaml
# .arklint.yml
version: "1"
extends:
  - arklint/fastapi
  - arklint/clean-arch
  - ./local-packs/my-company.yml   # local file packs also work

rules:
  # project-specific rules - these override pack rules with the same id
  - id: fastapi/no-db-in-routes
    type: boundary
    description: "Customised version of the pack rule"
    source: "api/**"
    blocked_imports: ["sqlalchemy", "psycopg2", "motor"]
    severity: error
```

## Local packs

Point `extends` at a relative path to share rules across a monorepo:

```yaml
extends:
  - ../../shared/arklint-rules.yml
```

The referenced file must have the same structure as a named pack - a `rules:` list at the top level.

## Contributing a pack

See [packs/CONTRIBUTING.md](https://github.com/Kaushik13k/arklint/blob/main/packs/CONTRIBUTING.md) for the full guide. No Python required - just YAML.
