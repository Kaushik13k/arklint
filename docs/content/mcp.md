# MCP Server

Expose your architectural rules to AI agents via the Model Context Protocol. AI coding tools can check code *before* writing it.

```bash
$ pip install 'arklint[mcp]'
$ arklint mcp
```

## Available tools

- **list_rules** — Returns all configured rules from `.arklint.yml` with full config details.
- **get_rule_details** — Inspect a single rule's full configuration by its ID.
- **check_file** — Validate an existing file against all rules and return violations.
- **check_snippet** — Validate a code snippet before writing it to disk. Supports virtual paths for path-based rules.

The `check_snippet` tool is especially powerful — an AI agent can validate code *before* committing it, using the `filename` parameter to control which path-based rules apply (e.g. passing `routes/user.py` triggers boundary rules).

## Claude Code / Cursor integration

```json
{
  "mcpServers": {
    "arklint": {
      "command": "arklint",
      "args": ["mcp"]
    }
  }
}
```
