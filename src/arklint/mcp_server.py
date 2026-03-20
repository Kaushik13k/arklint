"""MCP server for arklint.

Exposes arklint rules and checks to AI agents over the Model Context Protocol
using stdio transport.

Usage:
    arklint mcp

An AI agent that connects to this server can:
  - list_rules        → understand what architecture rules are in force
  - get_rule_details  → inspect one rule's full config
  - check_file        → validate an existing file against all rules
  - check_snippet     → validate a code snippet before writing it to disk
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from arklint.config import ConfigError, load_config
from arklint.engine import run_rules


def create_server(config_path: Path | None = None) -> "FastMCP":
    from mcp.server.fastmcp import FastMCP  # optional dependency

    mcp = FastMCP("arklint")

    # ------------------------------------------------------------------
    # Tool 1: list_rules
    # ------------------------------------------------------------------
    @mcp.tool()
    def list_rules(config: str | None = None) -> str:
        """Return all configured arklint rules from .arklint.yml.

        Args:
            config: Absolute path to a .arklint.yml file.
                    Auto-discovered from cwd upward if omitted.

        Returns:
            JSON array of rule objects with id, type, description, severity,
            and the full raw config dict.
        """
        cfg_path = Path(config) if config else config_path
        try:
            cfg = load_config(cfg_path)
        except ConfigError as exc:
            return json.dumps({"error": str(exc)})

        return json.dumps(
            [
                {
                    "id": r.id,
                    "type": r.type,
                    "description": r.description,
                    "severity": r.severity,
                    "config": r.raw,
                }
                for r in cfg.rules
            ],
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 2: get_rule_details
    # ------------------------------------------------------------------
    @mcp.tool()
    def get_rule_details(rule_id: str, config: str | None = None) -> str:
        """Return the full configuration of a single rule by its ID.

        Args:
            rule_id: The rule ID as defined in .arklint.yml (e.g. "no-print-statements").
            config: Absolute path to a .arklint.yml file. Auto-discovered if omitted.

        Returns:
            JSON object for the matching rule, or {"error": "..."} if not found.
        """
        cfg_path = Path(config) if config else config_path
        try:
            cfg = load_config(cfg_path)
        except ConfigError as exc:
            return json.dumps({"error": str(exc)})

        for r in cfg.rules:
            if r.id == rule_id:
                return json.dumps(
                    {
                        "id": r.id,
                        "type": r.type,
                        "description": r.description,
                        "severity": r.severity,
                        "config": r.raw,
                    },
                    indent=2,
                )

        return json.dumps({"error": f"Rule '{rule_id}' not found."})

    # ------------------------------------------------------------------
    # Tool 3: check_file
    # ------------------------------------------------------------------
    @mcp.tool()
    def check_file(file_path: str, config: str | None = None) -> str:
        """Run arklint rules against an existing file and return any violations.

        Args:
            file_path: Absolute path to the file to check.
            config: Absolute path to a .arklint.yml file. Auto-discovered if omitted.

        Returns:
            JSON object with:
              - "file": path checked
              - "violations": list of {rule, severity, line, message}
              - "passed": bool
        """
        cfg_path = Path(config) if config else config_path
        path = Path(file_path)

        if not path.exists():
            return json.dumps({"error": f"File not found: {file_path}"})
        if not path.is_file():
            return json.dumps({"error": f"Not a file: {file_path}"})

        try:
            cfg = load_config(cfg_path)
        except ConfigError as exc:
            return json.dumps({"error": str(exc)})

        results = run_rules(cfg, [path], scan_root=path.parent)
        violations = _collect_violations(results)

        return json.dumps(
            {"file": str(path), "violations": violations, "passed": not violations},
            indent=2,
        )

    # ------------------------------------------------------------------
    # Tool 4: check_snippet
    # ------------------------------------------------------------------
    @mcp.tool()
    def check_snippet(
        code: str,
        filename: str = "snippet.py",
        config: str | None = None,
    ) -> str:
        """Check a raw code snippet against arklint rules without writing a real file.

        The snippet is written to a temporary file under a virtual path matching
        *filename*, so path-based rules (boundary, layer-boundary) evaluate it
        as if it lives at that path in your project.

        Args:
            code: Source code string to check.
            filename: Virtual relative path for the snippet (e.g. "routes/user.py").
                      Controls which path-based rules apply.
            config: Absolute path to a .arklint.yml file. Auto-discovered if omitted.

        Returns:
            JSON object with:
              - "filename": virtual filename used
              - "violations": list of {rule, severity, line, message}
              - "passed": bool
        """
        cfg_path = Path(config) if config else config_path
        try:
            cfg = load_config(cfg_path)
        except ConfigError as exc:
            return json.dumps({"error": str(exc)})

        tmp_dir = Path(tempfile.mkdtemp())
        try:
            target = tmp_dir / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(code, encoding="utf-8")

            results = run_rules(cfg, [target], scan_root=tmp_dir)
            violations = _collect_violations(results)

            return json.dumps(
                {"filename": filename, "violations": violations, "passed": not violations},
                indent=2,
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return mcp


def _collect_violations(results) -> list[dict]:
    violations = []
    for result in results:
        for v in result.violations:
            violations.append(
                {
                    "rule": v.rule_id,
                    "severity": v.severity,
                    "line": v.line,
                    "message": v.message,
                }
            )
    return violations


def run_stdio(config_path: Path | None = None) -> None:
    """Launch the MCP server with stdio transport (blocking)."""
    server = create_server(config_path)
    server.run()
