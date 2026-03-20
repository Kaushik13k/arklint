"""Arklint CLI entry point.

Commands
--------
arklint init    Create a starter .arklint.yml in the current directory.
arklint check   Scan the codebase against all configured rules.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from arklint import __version__
from arklint.config import load_config, ConfigError
from arklint.engine import run_rules
from arklint.init_templates import STARTER_TEMPLATE
from arklint.reporter import console, err_console, emit_github_annotations, print_header, print_report
from arklint.scanner import collect_diff_files, collect_files


app = typer.Typer(
    name="arklint",
    help="The architectural rulebook for your codebase. Prevention, not detection.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


# ---------------------------------------------------------------------------
# arklint init
# ---------------------------------------------------------------------------

@app.command()
def init(
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite an existing .arklint.yml."
    ),
) -> None:
    """Create a starter [bold].arklint.yml[/bold] in the current directory."""
    target = Path.cwd() / ".arklint.yml"

    if target.exists() and not force:
        err_console.print(
            "[yellow].arklint.yml already exists.[/yellow] "
            "Use [bold]--force[/bold] to overwrite."
        )
        raise typer.Exit(1)

    target.write_text(STARTER_TEMPLATE)
    console.print(
        "[bold green]✓[/bold green] Created [cyan].arklint.yml[/cyan] with starter rules.\n"
        "  Edit it to match your architecture, then run [bold]arklint check[/bold]."
    )


# ---------------------------------------------------------------------------
# arklint check
# ---------------------------------------------------------------------------

@app.command()
def check(
    path: Optional[Path] = typer.Argument(
        None,
        help="Directory to scan. Defaults to the current directory.",
        show_default=False,
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to .arklint.yml. Auto-discovered if omitted.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Treat warnings as errors (exit code 1).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit violations as JSON (useful for CI integrations).",
    ),
    diff: Optional[str] = typer.Option(
        None,
        "--diff",
        metavar="BASE",
        help="Only scan files changed vs BASE (e.g. HEAD, origin/main).",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress passing rules — only show failures and warnings.",
    ),
    github_annotations: bool = typer.Option(
        False,
        "--github-annotations",
        help="Emit GitHub Actions workflow commands for inline PR annotations.",
    ),
) -> None:
    """Scan the codebase against your architectural rules."""
    scan_root = (path or Path.cwd()).resolve()

    try:
        cfg = load_config(config)
    except ConfigError as exc:
        err_console.print(f"[bold red]Config error:[/bold red] {exc}")
        raise typer.Exit(2) from exc

    if diff is not None:
        files = collect_diff_files(scan_root, base=diff)
        if not files:
            console.print("[dim]No changed files to scan.[/dim]")
            return
    else:
        files = collect_files(scan_root)

    if json_output:
        _check_json(cfg, files, scan_root, strict, diff_base=diff)
        return

    print_header(__version__, len(files), len(cfg.rules))
    results = run_rules(cfg, files, scan_root=scan_root)
    errors, warnings = print_report(results, scan_root, quiet=quiet)

    if github_annotations:
        emit_github_annotations(results, scan_root)

    if errors > 0 or (strict and warnings > 0):
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# arklint watch
# ---------------------------------------------------------------------------

@app.command()
def watch(
    path: Optional[Path] = typer.Argument(
        None,
        help="Directory to watch. Defaults to the current directory.",
        show_default=False,
    ),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to .arklint.yml.",
    ),
    strict: bool = typer.Option(
        False, "--strict", help="Treat warnings as errors.",
    ),
) -> None:
    """Watch for file changes and re-run checks automatically."""
    try:
        from watchdog.events import FileSystemEvent, FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:  # pragma: no cover
        err_console.print(
            "[bold red]watchdog is required for watch mode.[/bold red]\n"
            "Install it with: [bold]pip install watchdog[/bold]"
        )
        raise typer.Exit(1)

    import time

    scan_root = (path or Path.cwd()).resolve()

    try:
        cfg = load_config(config)
    except ConfigError as exc:
        err_console.print(f"[bold red]Config error:[/bold red] {exc}")
        raise typer.Exit(2) from exc

    def _run() -> None:
        console.rule("[dim]arklint[/dim]")
        files = collect_files(scan_root)
        print_header(__version__, len(files), len(cfg.rules))
        results = run_rules(cfg, files, scan_root=scan_root)
        errors, warnings = print_report(results, scan_root)
        if errors > 0 or (strict and warnings > 0):
            console.print("[bold red]✗ violations found[/bold red]")
        else:
            console.print("[bold green]✓ all rules passed[/bold green]")

    class _Handler(FileSystemEventHandler):
        def on_any_event(self, event: FileSystemEvent) -> None:
            if event.is_directory:
                return
            src = str(event.src_path)
            # ignore hidden dirs, caches, build artefacts
            if any(part.startswith(".") or part in ("__pycache__", "dist", "build")
                   for part in Path(src).parts):
                return
            _run()

    _run()
    console.print(f"\n[dim]Watching [cyan]{scan_root}[/cyan] — press Ctrl+C to stop.[/dim]\n")

    observer = Observer()
    observer.schedule(_Handler(), str(scan_root), recursive=True)
    observer.start()
    try:
        while observer.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        console.print("\n[dim]Watch stopped.[/dim]")


# ---------------------------------------------------------------------------
# arklint validate
# ---------------------------------------------------------------------------

@app.command()
def validate(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to .arklint.yml. Auto-discovered if omitted.",
    ),
) -> None:
    """Validate [bold].arklint.yml[/bold] without running any checks."""
    try:
        cfg = load_config(config)
    except ConfigError as exc:
        err_console.print(f"[bold red]✗ Invalid config:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    console.print(
        f"[bold green]✓ Valid[/bold green] — "
        f"[bold]{len(cfg.rules)}[/bold] rule{'s' if len(cfg.rules) != 1 else ''} loaded "
        f"from [cyan]{cfg.root / '.arklint.yml'}[/cyan]"
    )


# ---------------------------------------------------------------------------
# arklint mcp
# ---------------------------------------------------------------------------

@app.command()
def mcp(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to .arklint.yml. Auto-discovered if omitted.",
    ),
) -> None:
    """Start the arklint MCP server (stdio transport) for AI agent integration."""
    try:
        from arklint.mcp_server import run_stdio
    except ImportError:
        err_console.print(
            "[bold red]mcp package is required for MCP server mode.[/bold red]\n"
            "Install it with: [bold]pip install 'arklint[mcp]'[/bold]"
        )
        raise typer.Exit(1)

    run_stdio(config_path=config)


# ---------------------------------------------------------------------------
# --version flag (attached to the root callback)
# ---------------------------------------------------------------------------

@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v", is_eager=True, help="Show version and exit."
    ),
) -> None:
    if version:
        console.print(f"arklint v{__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


# ---------------------------------------------------------------------------
# JSON output helper
# ---------------------------------------------------------------------------

def _check_json(cfg, files, scan_root, strict: bool, diff_base: str | None = None) -> None:
    import json

    results = run_rules(cfg, files, scan_root=scan_root)
    output = []
    errors = 0
    warnings = 0
    for result in results:
        for v in result.violations:
            try:
                rel = str(v.file.relative_to(scan_root))
            except ValueError:
                rel = str(v.file)
            output.append(
                {
                    "rule": v.rule_id,
                    "severity": v.severity,
                    "file": rel,
                    "line": v.line,
                    "message": v.message,
                }
            )
            if v.severity == "error":
                errors += 1
            else:
                warnings += 1

    console.print(json.dumps(output, indent=2))
    if errors > 0 or (strict and warnings > 0):
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    app()


if __name__ == "__main__":
    main()
