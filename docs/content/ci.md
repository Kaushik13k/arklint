# CI / Pre-commit

Block architectural violations automatically on every push or commit.

## GitHub Actions

The simplest setup - add Arklint to any existing workflow:

```yaml
- name: Run Arklint
  run: |
    pip install arklint
    arklint check --strict
```

For large repos, use diff mode to only scan changed files:

```yaml
- name: Run Arklint (diff)
  run: |
    pip install arklint
    arklint check --diff origin/main --strict --github-annotations
```

The `--github-annotations` flag emits inline PR annotations so violations appear directly on the changed lines in the pull request.

> **Tip:** For faster installs, use the [GitHub Action](#action) directly - it handles caching and version pinning automatically.

## pre-commit hook

Add to your `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: arklint
      name: Arklint
      entry: arklint check
      language: python
      pass_filenames: false
```

Install the hook:

```bash
$ pre-commit install
```

## GitLab CI

```yaml
arklint:
  stage: lint
  image: python:3.11-slim
  script:
    - pip install arklint
    - arklint check --strict
```

## CircleCI

```yaml
- run:
    name: Arklint
    command: |
      pip install arklint
      arklint check --strict
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed |
| `1` | One or more errors (or warnings with `--strict`) |
| `2` | Config file invalid or not found |

All CI systems treat a non-zero exit code as a pipeline failure.
