# Watch Mode

Get instant feedback as you code. Arklint re-runs checks on every file save.

```bash
$ arklint watch
$ arklint watch ./src --strict
```

Watch mode uses `watchdog` to monitor filesystem events. It automatically ignores hidden directories, `__pycache__`, `dist`, and `build` folders. Press **Ctrl+C** to stop.
