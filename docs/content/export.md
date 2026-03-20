# Export Rules

Export your `.arklint.yml` rules as AI assistant instruction files so your coding tools respect the same architectural constraints.

```bash
$ arklint export --format cursorrules
$ arklint export --format claude
$ arklint export --format copilot
```

## Formats

| Format | Output file | Used by |
|--------|-------------|---------|
| `cursorrules` | `.cursorrules` | Cursor IDE |
| `claude` | `CLAUDE.md` | Claude Code |
| `copilot` | `.github/copilot-instructions.md` | GitHub Copilot |

Each file lists your rules with severity tags (`[ERROR]` / `[WARN]`) and descriptions in a format the AI understands natively.

## Options

| Flag | Description |
|------|-------------|
| `--format` / `-f` | Output format (required): `cursorrules`, `claude`, or `copilot` |
| `--output` / `-o` | Directory to write into. Defaults to current directory |
| `--config` / `-c` | Path to `.arklint.yml`. Auto-discovered if omitted |

## Example

```bash
$ arklint export --format claude --output .
```

This writes `CLAUDE.md` in your project root. Claude Code will automatically pick it up on the next session and respect your architectural rules when generating code.

> Re-run `arklint export` whenever you update your rules to keep the AI instruction files in sync.
