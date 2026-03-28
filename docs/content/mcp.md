# MCP Server

Expose your architectural rules to AI agents via the Model Context Protocol. AI coding tools can check code *before* writing it - and refuse to generate violations automatically.

```bash
$ pip install 'arklint[mcp]'
$ arklint mcp
```

> The MCP server is bundled in the npm and .NET prebuilt binaries. No extra install needed - run `arklint mcp` directly.

## Available tools

- **list_rules** - Returns all configured rules from `.arklint.yml` with full config details.
- **get_rule_details** - Inspect a single rule's full configuration by its ID.
- **check_file** - Validate an existing file against all rules and return violations.
- **check_snippet** - Validate a code snippet before writing it to disk. Supports virtual paths for path-based rules.

The `check_snippet` tool is especially powerful: an AI agent validates code *before* it exists on disk. Pass a `filename` parameter (e.g. `routes/user.py`) so that path-based rules like `boundary` and `file-pattern` apply correctly.

## Claude Code integration

Add to your Claude Code config (`.claude/settings.json` or `~/.claude/settings.json`):

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

Once connected, Claude Code calls `check_snippet` automatically before writing files that match your rules.

## Cursor integration

Add to your Cursor MCP config (`.cursor/mcp.json`):

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

## Pair with export for best results

The MCP server handles runtime checks. For AI agents to *understand* your rules and avoid writing violations in the first place, also export your rules as native AI instructions:

```bash
$ arklint export --format claude      # writes CLAUDE.md
$ arklint export --format cursorrules # writes .cursorrules
```

This two-layer approach - instructions at generation time, MCP validation at write time - gives the strongest architecture enforcement with AI tools.

> Re-run `arklint export` whenever you update your rules to keep the AI instruction files in sync.
