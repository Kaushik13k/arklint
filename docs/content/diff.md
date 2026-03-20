# Diff Mode

Only scan files that changed — perfect for large codebases and CI on pull requests.

```bash
$ arklint check --diff HEAD            # staged + unstaged changes
$ arklint check --diff origin/main     # changes vs main branch
```

Diff mode runs `git diff --name-only` under the hood, including both staged and unstaged changes. Only the changed files are scanned against your rules.
