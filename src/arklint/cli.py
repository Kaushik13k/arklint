"""Arklint CLI entry point.

Commands
--------
arklint init    Create a starter .arklint.yml in the current directory.
arklint check   Scan the codebase against all configured rules.
arklint export  Export rules as AI assistant instruction files.
"""
from __future__ import annotations

import time
from pathlib import Path

import typer
import yaml

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
    path: Path | None = typer.Argument(
        None,
        help="Directory to scan. Defaults to the current directory.",
        show_default=False,
    ),
    config: Path | None = typer.Option(
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
    diff: str | None = typer.Option(
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

    if errors > 0:
        console.print("[bold red]✗ violations found[/bold red]")
        raise typer.Exit(1)
    elif strict and warnings > 0:
        console.print("[bold red]✗ warnings treated as errors (--strict)[/bold red]")
        raise typer.Exit(1)
    elif warnings > 0:
        console.print("[bold yellow]⚠ warnings found — run with --strict to fail on warnings[/bold yellow]")
    else:
        console.print("[bold green]✓ all rules passed[/bold green]")


# ---------------------------------------------------------------------------
# arklint watch
# ---------------------------------------------------------------------------

@app.command()
def watch(
    path: Path | None = typer.Argument(
        None,
        help="Directory to watch. Defaults to the current directory.",
        show_default=False,
    ),
    config: Path | None = typer.Option(
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
        if errors > 0:
            console.print("[bold red]✗ violations found[/bold red]")
<<<<<<< Updated upstream
=======
        elif strict and warnings > 0:
            console.print("[bold red]✗ warnings treated as errors (--strict)[/bold red]")
>>>>>>> Stashed changes
        elif warnings > 0:
            console.print("[bold yellow]⚠ warnings — run with --strict to treat as errors[/bold yellow]")
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
    config: Path | None = typer.Option(
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
# arklint export
# ---------------------------------------------------------------------------

@app.command()
def export(
    fmt: str = typer.Option(
        ...,
        "--format",
        "-f",
        help="Output format: cursorrules, claude, or copilot.",
        metavar="FORMAT",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to .arklint.yml. Auto-discovered if omitted.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Directory to write the file into. Defaults to the current directory.",
    ),
) -> None:
    """Export rules as an AI assistant instruction file.

    Formats:
      [bold]cursorrules[/bold]  →  .cursorrules
      [bold]claude[/bold]       →  CLAUDE.md
      [bold]copilot[/bold]      →  .github/copilot-instructions.md
    """
    from arklint.exporter import export as do_export, SUPPORTED_FORMATS

    if fmt not in SUPPORTED_FORMATS:
        err_console.print(
            f"[bold red]Unknown format:[/bold red] {fmt!r}. "
            f"Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )
        raise typer.Exit(1)

    try:
        cfg = load_config(config)
    except ConfigError as exc:
        err_console.print(f"[bold red]Config error:[/bold red] {exc}")
        raise typer.Exit(2) from exc

    out_dir = (output or Path.cwd()).resolve()
    dest = do_export(cfg, fmt, out_dir)

    console.print(
        f"[bold green]✓ Exported[/bold green] [bold]{len(cfg.rules)}[/bold] "
        f"rule{'s' if len(cfg.rules) != 1 else ''} → [cyan]{dest}[/cyan]"
    )


# ---------------------------------------------------------------------------
# arklint learn
# ---------------------------------------------------------------------------

@app.command()
def learn(
    describe: str = typer.Option(
        ...,
        "--describe",
        "-d",
        help="Plain-English description of the rule you want to enforce.",
        metavar="TEXT",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to .arklint.yml to append the rule to. Auto-discovered if omitted.",
    ),
    provider: str = typer.Option(
        ...,
        "--provider",
        "-p",
        help="AI provider to use: anthropic or openai.",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        help="API key for the chosen provider. Falls back to ANTHROPIC_API_KEY or OPENAI_API_KEY.",
        show_default=False,
    ),
    append: bool = typer.Option(
        False,
        "--append",
        "-a",
        help="Automatically append the suggested rule to .arklint.yml without prompting.",
    ),
) -> None:
    """Generate an arklint rule from a plain-English description using AI.

    Examples:

      arklint learn --describe "no raw SQL in routes" --provider anthropic

      arklint learn --describe "no raw SQL in routes" --provider openai
    """
    from arklint.learner import suggest_rule, SUPPORTED_PROVIDERS

    if provider not in SUPPORTED_PROVIDERS:
        err_console.print(
            f"[bold red]Unknown provider:[/bold red] {provider!r}. "
            f"Choose from: {', '.join(SUPPORTED_PROVIDERS)}"
        )
        raise typer.Exit(1)

    console.print(f"[dim]Generating rule via {provider}…[/dim]")

    try:
        yaml_snippet = suggest_rule(description=describe, provider=provider, api_key=api_key)
    except ImportError as exc:
        err_console.print(f"[bold red]Missing dependency:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    except ValueError as exc:
        err_console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        raise typer.Exit(1) from exc
    except RuntimeError as exc:
        err_console.print(f"[bold red]API error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    console.print("\n[bold cyan]Suggested rule:[/bold cyan]\n")
    console.print(yaml_snippet)
    console.print()

    if not append:
        confirm = typer.confirm("Append this rule to .arklint.yml?")
        if not confirm:
            console.print("[dim]Aborted — rule not saved.[/dim]")
            return

    try:
        cfg_path = config or _find_config_path()
    except FileNotFoundError as exc:
        err_console.print(f"[bold red]Config error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    with open(cfg_path, "a", encoding="utf-8") as f:
        with open(cfg_path, "a", encoding="utf-8") as f:
            indented_snippet = yaml_snippet.replace("\n", "\n  ")
            f.write("\n  " + indented_snippet + "\n")

    console.print(
        f"[bold green]✓ Rule appended[/bold green] to [cyan]{cfg_path}[/cyan]\n"
        f"  Run [bold]arklint validate[/bold] to confirm the config is valid."
    )


def _find_config_path() -> Path:
    """Return the path to .arklint.yml, raising FileNotFoundError if absent."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / ".arklint.yml"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "No .arklint.yml found. Run 'arklint init' to create one."
    )


# ---------------------------------------------------------------------------
# arklint search
# ---------------------------------------------------------------------------

@app.command()
def search(
    query: str = typer.Argument(
        ...,
        help="Search term — e.g. 'fastapi', 'django', 'clean-arch'.",
        metavar="QUERY",
    ),
) -> None:
    """Search available official rule packs."""
    from arklint.packs import search_packs, PackError

    try:
        results = search_packs(query)
    except PackError as exc:
        err_console.print(f"[bold red]Registry error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    if not results:
        console.print(f"[yellow]No packs found matching '{query}'.[/yellow]")
        raise typer.Exit(0)

    console.print(f"\n[bold]Packs matching '{query}':[/bold]\n")
    for pack in results:
        console.print(
            f"  [bold cyan]{pack['name']}[/bold cyan]  "
            f"[dim]({pack.get('rules', '?')} rules)[/dim]\n"
            f"  {pack.get('description', '')}\n"
        )
    console.print(f"[dim]Add a pack with: arklint add <name>[/dim]")


# ---------------------------------------------------------------------------
# arklint add
# ---------------------------------------------------------------------------

@app.command()
def add(
    pack: str = typer.Argument(
        ...,
        help="Pack name to add — e.g. 'arklint/fastapi'.",
        metavar="PACK",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to .arklint.yml. Auto-discovered if omitted.",
    ),
) -> None:
    """Add an official rule pack to your .arklint.yml."""
    from arklint.packs import resolve_pack, PackError

    # resolve and validate config path
    try:
        cfg_path = config or _find_config_path()
    except FileNotFoundError as exc:
        err_console.print(f"[bold red]Config error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    if not cfg_path.exists():
        err_console.print(f"[bold red]Config not found:[/bold red] {cfg_path}")
        raise typer.Exit(1)

    try:
        raw_cfg = yaml.safe_load(cfg_path.read_text())
    except yaml.YAMLError as exc:
        err_console.print(f"[bold red]Invalid YAML in config:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    if not isinstance(raw_cfg, dict):
        err_console.print("[bold red]Config error:[/bold red] .arklint.yml must be a YAML mapping.")
        raise typer.Exit(1)

    extends: list = raw_cfg.get("extends", [])
    if not isinstance(extends, list):
        err_console.print("[bold red]Config error:[/bold red] 'extends' must be a list.")
        raise typer.Exit(1)

    if pack in extends:
        console.print(f"[yellow]'{pack}' is already in extends.[/yellow]")
        raise typer.Exit(0)

    # verify the pack resolves before writing
    console.print(f"[dim]Fetching pack '{pack}'…[/dim]")
    try:
        rules = resolve_pack(pack, cfg_path.parent)
    except PackError as exc:
        err_console.print(f"[bold red]Pack error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    # safe YAML rewrite — no text surgery
    raw_cfg["extends"] = extends + [pack]
    cfg_path.write_text(yaml.dump(raw_cfg, default_flow_style=False, sort_keys=False))

    console.print(
        f"[bold green]✓ Added[/bold green] [cyan]{pack}[/cyan] "
        f"([bold]{len(rules)}[/bold] rules) to [cyan]{cfg_path}[/cyan]\n"
        f"  Run [bold]arklint validate[/bold] to confirm."
    )


# ---------------------------------------------------------------------------
# arklint mcp
# ---------------------------------------------------------------------------

@app.command()
def mcp(
    config: Path | None = typer.Option(
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
# arklint visualize
# ---------------------------------------------------------------------------

@app.command()
def visualize(
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to .arklint.yml. Auto-discovered if omitted.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write diagram to a file instead of printing to stdout.",
    ),
) -> None:
    """Generate a Mermaid diagram of your architecture rules.

    Paste the output into any Markdown file or visit [bold]mermaid.live[/bold]
    to render it interactively.
    """
    from arklint.visualize import build_mermaid

    try:
        cfg = load_config(config)
    except ConfigError as exc:
        err_console.print(f"[bold red]Config error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    diagram = build_mermaid(cfg)

    if output:
        output.write_text(diagram)
        console.print(f"[bold green]✓[/bold green] Diagram written to [cyan]{output}[/cyan]")
    else:
        console.print(diagram)


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
