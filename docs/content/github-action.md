# GitHub Action

Use Arklint as a first-class GitHub Action with built-in diff mode, inline PR annotations, version pinning, and strict mode.

```yaml
- uses: Kaushik13k/ark-lint@main
  with:
    strict: "true"
    diff: "origin/main"
```

## Full example

```yaml
name: Arklint

on:
  pull_request:
  push:
    branches: [main]

jobs:
  arklint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # needed for diff mode

      - uses: Kaushik13k/ark-lint@main
        with:
          strict: "true"
          diff: "origin/main"
```

> Set `fetch-depth: 0` in `actions/checkout` so the full git history is available for diff mode. Without it, `origin/main` may not be resolvable.

## Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `version` | Arklint version to install. Pin for reproducible builds. | `latest` |
| `strict` | Treat warnings as errors (`"true"` / `"false"`) | `"false"` |
| `diff` | Only scan files changed vs this ref (e.g. `origin/main`) | (all files) |
| `config` | Path to `.arklint.yml`. Auto-discovered from project root if omitted. | (auto) |
| `working-directory` | Directory to run arklint in, for monorepos | `.` |

## Inline PR annotations

When `diff` mode is enabled, the action automatically passes `--github-annotations` to emit inline annotations on the pull request. Violations appear directly on the changed lines — no need to scroll through logs.
