# Watch Mode

Re-run architecture checks automatically on every file save. Get instant feedback without switching to a terminal.

```bash
$ arklint watch
$ arklint watch ./src
$ arklint watch --strict
```

## How it works

Watch mode uses `watchdog` to monitor filesystem events in your project directory. On every file change, Arklint re-runs all checks and prints the updated results.

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
| `--strict` | Treat warnings as errors |
| `-c / --config <path>` | Use a config file from a custom path |

## Typical usage

Run it once when you start coding and leave it in the background. Any violation you introduce shows up immediately.

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
