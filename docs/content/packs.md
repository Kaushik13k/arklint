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
✓ Added arklint/fastapi (4 rules) to .arklint.yml
  Run arklint validate to confirm.
```

This appends the pack to the `extends` list in your `.arklint.yml`. Your own rules always take precedence - if you define a rule with the same `id` as a pack rule, yours wins.

## Official packs

| Pack | Rules | Description |
|------|-------|-------------|
| `arklint/fastapi` | 4 | FastAPI service/route/schema separation, single HTTP client |
| `arklint/django` | 4 | Django model/view/serializer placement, no raw SQL in views |
| `arklint/nextjs` | 3 | Next.js server/client boundary, no DB in server actions |
| `arklint/express` | 3 | Express route/service separation, no console.log in prod |
| `arklint/clean-arch` | 2 | Clean architecture layer ordering, no framework in entities |

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
