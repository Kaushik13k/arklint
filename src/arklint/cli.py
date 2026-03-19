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
from arklint.reporter import console, err_console, print_header, print_report
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
    errors, warnings = print_report(results, scan_root)

    if errors > 0 or (strict and warnings > 0):
        raise typer.Exit(1)


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
