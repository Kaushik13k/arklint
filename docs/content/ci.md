# CI / Pre-commit

Enforce rules automatically on every push or commit.

## GitHub Actions

```yaml
- name: Arklint
  run: |
    pip install arklint
    arklint check --strict
```

## pre-commit hook

```yaml
- repo: local
  hooks:
    - id: arklint
      name: arklint
      entry: arklint check
      language: python
      pass_filenames: false
```
