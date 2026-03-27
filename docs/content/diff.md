# Diff Mode

Scan only the files that changed — not the entire codebase. Keeps CI fast on large repositories and makes PR checks precise.

```bash
$ arklint check --diff HEAD             # staged + unstaged changes vs HEAD
$ arklint check --diff origin/main      # files changed on your branch vs main
$ arklint check --diff main --strict    # fail on warnings too
```

## How it works

Diff mode runs `git diff --name-only <ref>` under the hood to get the list of changed files, then restricts scanning to only those files. All rules still apply — only the file set is narrowed.

This means:
- A `boundary` rule only fires if a *changed* file has the forbidden import
- A `pattern-ban` rule only fires on *changed* files
- `dependency` rules always scan the full dependency file (since any change can introduce a conflict)

## Why use it

On a repo with thousands of files, `arklint check` scans everything every run. In CI, that can be slow. With `--diff origin/main`, only the files touched by the pull request are scanned — which is usually the right scope anyway.

```bash
# In CI: only check what this PR changed
arklint check --diff origin/main --strict --github-annotations
```

## Options

| Flag | Description |
|------|-------------|
| `--diff <ref>` | Git ref to diff against (`HEAD`, `origin/main`, a commit SHA, etc.) |
| `--strict` | Treat warnings as errors |
| `--json` | Machine-readable JSON output |
| `--github-annotations` | Emit inline PR annotations (for use inside GitHub Actions) |

> Diff mode requires a git repository. The `--diff` flag is ignored if no `.git` directory is found.
