# Contributing to Arklint

Thank you for your interest in contributing. This document explains how to get set up, what the standards are, and how the review process works.

---

## Ground rules

- Every change goes through a pull request — no direct pushes to `main`.
- Every PR needs at least one approval from a CODEOWNER before merging.
- Every source change (`src/`) must be accompanied by a test in `tests/`.
- All CI checks must be green before a PR can merge.

---

## Getting started

```bash
git clone https://github.com/Kaushik13k/arklint
cd arklint
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Run the tests:

```bash
pytest -v
```

Run arklint on itself:

```bash
arklint check
```

---

## Making a change

1. **Create a branch** from `main`:
   ```bash
   git checkout -b your-branch-name
   ```

2. **Make your changes** — follow the existing code style (no external linters enforced beyond arklint itself).

3. **Write tests** — every new behaviour and every bug fix needs a test under `tests/`.

4. **Run CI locally** before pushing:
   ```bash
   pytest -v
   arklint check
   ```

5. **Open a pull request** — the PR template will prompt you for what, why, and how it was tested. Fill it in.

---

## Pull request checklist

The PR template includes this checklist — all items must be checked before review:

- Tests added or updated for every change
- `arklint check` passes locally
- No hardcoded secrets or API keys
- README updated if behaviour or CLI changed

---

## Adding a new rule type

1. Create `src/arklint/rules/your_rule.py` — implement `BaseRule` (see `rules/base.py`).
2. Register it in `src/arklint/rules/__init__.py`.
3. Register it in `src/arklint/engine.py` (the `RULE_REGISTRY` dict).
4. Add a YAML example to `src/arklint/init_templates.py`.
5. Document it in `README.md`.
6. Add tests under `tests/test_rules/test_your_rule.py`.

---

## Commit style

Use the conventional commit format:

```
feat: add --quiet flag to suppress passing rules
fix: deduplicate boundary violations per file
docs: update CLI reference for --diff mode
test: add layer-boundary violation deduplication test
refactor: extract _rel() helper to BaseRule
```

---

## Branch protection

The `main` branch is protected:

| Rule | Detail |
|---|---|
| Direct pushes blocked | All changes must go through a PR |
| CI must pass | pytest, arklint check, tests-changed |
| 1 approval required | Must be from a CODEOWNER |
| Stale reviews dismissed | New commits invalidate previous approvals |

---

## Reporting bugs

Open an issue at [github.com/Kaushik13k/arklint/issues](https://github.com/Kaushik13k/arklint/issues) with:

- Arklint version (`arklint --version`)
- Your `.arklint.yml` (or the relevant rule)
- The command you ran
- What you expected vs what happened

---

## License

By contributing you agree that your changes will be licensed under the MIT License.
