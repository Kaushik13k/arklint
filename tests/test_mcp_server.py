"""Tests for the MCP server tools.

These tests call the tool functions directly via the server object
without starting a real MCP process - no mcp package required at test time.
"""
from __future__ import annotations
from arklint.mcp_server import create_server

import json
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

mcp = pytest.importorskip(
    "mcp", reason="mcp package not installed; skipping MCP server tests")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_config(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".yml", delete=False, mode="w")
    tmp.write(textwrap.dedent(content))
    tmp.close()
    return Path(tmp.name)


def _write_file(content: str, suffix: str = ".py") -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode="w")
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


SIMPLE_CONFIG = """
    version: "1"
    rules:
      - id: no-print
        type: pattern-ban
        description: No raw print calls
        pattern: "print\\\\("
        severity: warning
      - id: no-todo
        type: pattern-ban
        description: No TODO comments
        pattern: "TODO"
        severity: error
"""


def _tool(server, name):
    """Return the callable for a registered tool by name."""
    for tool in server._tool_manager.list_tools():
        if tool.name == name:
            # FastMCP stores the underlying fn; call via the manager
            break
    # Access internal fn map directly for testing
    return server._tool_manager._tools[name].fn


# ---------------------------------------------------------------------------
# list_rules
# ---------------------------------------------------------------------------

class TestListRules:
    def test_returns_all_rules(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "list_rules")
        result = json.loads(fn())
        assert isinstance(result, list)
        assert len(result) == 2
        ids = [r["id"] for r in result]
        assert "no-print" in ids
        assert "no-todo" in ids

    def test_rule_has_expected_fields(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "list_rules")
        rules = json.loads(fn())
        rule = next(r for r in rules if r["id"] == "no-print")
        assert rule["type"] == "pattern-ban"
        assert rule["severity"] == "warning"
        assert rule["description"] == "No raw print calls"
        assert "config" in rule

    def test_missing_config_returns_error(self):
        server = create_server(config_path=Path("/nonexistent/.arklint.yml"))
        fn = _tool(server, "list_rules")
        result = json.loads(fn())
        assert "error" in result

    def test_config_override_param(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        server = create_server()  # no default config
        fn = _tool(server, "list_rules")
        result = json.loads(fn(config=str(cfg_path)))
        assert isinstance(result, list)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# get_rule_details
# ---------------------------------------------------------------------------

class TestGetRuleDetails:
    def test_existing_rule(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "get_rule_details")
        result = json.loads(fn(rule_id="no-todo"))
        assert result["id"] == "no-todo"
        assert result["severity"] == "error"

    def test_unknown_rule_returns_error(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "get_rule_details")
        result = json.loads(fn(rule_id="does-not-exist"))
        assert "error" in result
        assert "does-not-exist" in result["error"]


# ---------------------------------------------------------------------------
# check_file
# ---------------------------------------------------------------------------

class TestCheckFile:
    def test_clean_file_passes(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        file = _write_file("x = 1\n")
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "check_file")
        result = json.loads(fn(file_path=str(file)))
        assert result["passed"] is True
        assert result["violations"] == []

    def test_violation_detected(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        file = _write_file('print("hello")\n')
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "check_file")
        result = json.loads(fn(file_path=str(file)))
        assert result["passed"] is False
        assert len(result["violations"]) == 1
        assert result["violations"][0]["rule"] == "no-print"
        assert result["violations"][0]["severity"] == "warning"

    def test_nonexistent_file_returns_error(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "check_file")
        result = json.loads(fn(file_path="/no/such/file.py"))
        assert "error" in result

    def test_multiple_violations(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        file = _write_file('print("hi")  # TODO: remove\n')
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "check_file")
        result = json.loads(fn(file_path=str(file)))
        assert result["passed"] is False
        assert len(result["violations"]) == 2


# ---------------------------------------------------------------------------
# check_snippet
# ---------------------------------------------------------------------------

class TestCheckSnippet:
    def test_clean_snippet_passes(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "check_snippet")
        result = json.loads(fn(code="x = 1\n"))
        assert result["passed"] is True
        assert result["violations"] == []

    def test_snippet_with_violation(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "check_snippet")
        result = json.loads(fn(code='print("bad")\n'))
        assert result["passed"] is False
        assert result["violations"][0]["rule"] == "no-print"

    def test_virtual_filename_preserved_in_result(self):
        cfg_path = _write_config(SIMPLE_CONFIG)
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "check_snippet")
        result = json.loads(fn(code="x = 1\n", filename="routes/user.py"))
        assert result["filename"] == "routes/user.py"

    def test_temp_file_cleaned_up(self):
        """No temp files should remain after check_snippet."""
        import glob
        import os
        cfg_path = _write_config(SIMPLE_CONFIG)
        server = create_server(config_path=cfg_path)
        fn = _tool(server, "check_snippet")
        before = set(glob.glob(str(Path(tempfile.gettempdir()) / "tmp*")))
        fn(code="x = 1\n")
        after = set(glob.glob(str(Path(tempfile.gettempdir()) / "tmp*")))
        # Any dirs created by our code should be gone
        new_items = after - before
        assert not any(Path(p).is_dir() for p in new_items)
