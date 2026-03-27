"""Rich terminal reporter.

Accepts ``list[CheckResult]`` from the engine and produces a structured,
coloured terminal report.  The only public surface is :func:`print_report`.
"""
from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.text import Text

from arklint.engine import CheckResult


# Single shared console — callers can import this to print their own messages.
console = Console()
err_console = Console(stderr=True)

_DIVIDER = "─" * 52


def print_header(version: str, file_count: int, rule_count: int) -> None:
    console.print(
        f"\n[bold cyan]Arklint v{version}[/bold cyan] [dim]—[/dim] "
        f"Scanning [bold]{file_count}[/bold] files against "
        f"[bold]{rule_count}[/bold] rule{'s' if rule_count != 1 else ''}...\n"
    )


def print_report(
    results: list[CheckResult],
    scan_root: Path,
    quiet: bool = False,
) -> tuple[int, int]:
    """Render all results to the terminal.

    When *quiet* is True, passing rules are suppressed — only failures
    and warnings are printed.

    Returns ``(total_errors, total_warnings)``.
    """
    total_errors = 0
    total_warnings = 0

    for result in results:
        _render_result(result, scan_root, quiet=quiet)
        total_errors += result.error_count
        total_warnings += result.warning_count

    _render_summary(results, total_errors, total_warnings)
    return total_errors, total_warnings


# ---------------------------------------------------------------------------
# GitHub Actions annotations
# ---------------------------------------------------------------------------

def emit_github_annotations(
    results: list[CheckResult],
    scan_root: Path,
) -> None:
    """Write GitHub Actions workflow commands for every violation.

    Each line is picked up by the GitHub Actions runner and shown as an
    inline annotation on the PR diff — no API token required.
    """
    for result in results:
        for v in result.violations:
            level = "error" if v.severity == "error" else "warning"
            try:
                rel = str(v.file.relative_to(scan_root))
            except ValueError:
                rel = str(v.file)

            parts = [f"file={rel}"]
            if v.line:
                parts.append(f"line={v.line}")
            params = ",".join(parts)
            print(f"::{level} {params}::{v.rule_id}: {v.message}")


# ---------------------------------------------------------------------------
# Internal renderers
# ---------------------------------------------------------------------------

def _render_result(result: CheckResult, scan_root: Path, quiet: bool = False) -> None:
    if result.passed:
        if not quiet:
            console.print(f"  [bold green]✓ PASS[/bold green]  [dim]{result.rule.id}[/dim]")
        return

    severity = result.rule.severity
    if severity == "error":
        status = Text("✗ FAIL", style="bold red")
    else:
        status = Text("⚠ WARN", style="bold yellow")

    console.print(f"\n  {status}  [bold]{result.rule.id}[/bold]")
    if result.rule.description:
        console.print(f"         [dim]{result.rule.description}[/dim]")

    msg_color = "red" if severity == "error" else "yellow"

    for v in result.violations:
        try:
            rel_path = v.file.relative_to(scan_root)
        except ValueError:
            rel_path = v.file  # type: ignore[assignment]

        if v.file == scan_root:
            location = "[cyan](project)[/cyan]"
        elif v.line:
            location = f"[cyan]{rel_path}:{v.line}[/cyan]"
        else:
            location = f"[cyan]{rel_path}[/cyan]"

        console.print(f"         {location} [dim]→[/dim] [{msg_color}]{v.message}[/{msg_color}]")


def _render_summary(
    results: list[CheckResult], errors: int, warnings: int
) -> None:
    passed = sum(1 for r in results if r.passed)

    console.print()
    console.print(_DIVIDER)

    parts: list[str] = []
    if errors:
        parts.append(f"[bold red]{errors} error{'s' if errors != 1 else ''}[/bold red]")
    if warnings:
        parts.append(
            f"[bold yellow]{warnings} warning{'s' if warnings != 1 else ''}[/bold yellow]"
        )
    if passed:
        parts.append(
            f"[bold green]{passed} passed[/bold green]"
        )

    summary = ", ".join(parts) if parts else "[bold green]all rules passed[/bold green]"
    console.print(f"Results: {summary}")
    console.print(_DIVIDER)
    console.print()
