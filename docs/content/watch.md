# Watch Mode

Re-run architecture checks automatically on every file save. Get instant feedback without switching to a terminal.

```bash
$ arklint watch
$ arklint watch ./src
$ arklint watch --strict
```

## How it works

Watch mode uses `watchdog` to monitor filesystem events in your project directory. On every file change, Arklint re-runs all checks and prints the updated results — just like `arklint check`, but live.

**What triggers a re-run:**
- Any file save or creation in the watched directory tree
- Changes to `.arklint.yml` itself

**What is automatically ignored:**
- Hidden directories (`.git`, `.venv`, etc.)
- `__pycache__`, `dist`, `build`, `node_modules`

Press **Ctrl+C** to stop.

## Options

| Flag | Description |
|------|-------------|
| `<path>` | Directory to watch. Defaults to current directory |
| `--strict` | Treat warnings as errors (exit 1 on any warning) |
| `-c / --config <path>` | Use a config file from a custom path |

## Typical usage

Watch mode is most useful during active development on a feature branch — run it once when you start coding and leave it in the background. Any boundary violation or banned pattern you introduce shows up immediately, before you commit.

```bash
$ arklint watch ./src --strict
Watching ./src for changes…  (Ctrl+C to stop)

[12:34:01] Change detected — re-running checks…

  ✗ FAIL  no-direct-db-in-routes
         routes/orders.py → imports 'psycopg2' — blocked

[12:34:09] Change detected — re-running checks…

  ✓ PASS  no-direct-db-in-routes
  ✓ PASS  no-print-statements
  ✓ PASS  layered-architecture
```
