# GitHub Action

Use Arklint as a first-class GitHub Action with built-in diff mode, version pinning, and strict mode.

```yaml
- uses: Kaushik13k/ark-lint@main
  with:
    strict: "true"
    diff: "origin/main"
    version: "0.2.0"
```

## Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `version` | Arklint version to install. Defaults to latest. | latest |
| `strict` | Treat warnings as errors. | `false` |
| `diff` | Only scan files changed vs this ref. | (empty = all files) |
| `config` | Path to `.arklint.yml`. Auto-discovered if omitted. | (auto) |
| `working-directory` | Directory to run arklint in. | `.` |
