# CLI Reference

Every command and flag Arklint supports.

| Command | Description |
|---------|-------------|
| `arklint init` | Generate a starter `.arklint.yml` in the current directory |
| `arklint init --force` | Overwrite an existing config file |
| `arklint check` | Scan the codebase from the current directory |
| `arklint check <path>` | Scan a specific directory |
| `arklint check --strict` | Exit with code 1 on warnings (not just errors) |
| `arklint check --quiet` / `-q` | Suppress passing rules — only show failures and warnings |
| `arklint check --json` | Machine-readable JSON output for CI pipelines |
| `arklint check --diff <ref>` | Only scan files changed vs a git ref |
| `arklint check --github-annotations` | Emit GitHub Actions inline PR annotations |
| `arklint check -c <path>` | Use a config file from a custom path |
| `arklint validate` | Validate `.arklint.yml` without running any checks |
| `arklint validate -c <path>` | Validate a config file at a custom path |
| `arklint search <query>` | Search official rule packs by name, description, or tag |
| `arklint add <pack>` | Add an official rule pack to `.arklint.yml` |
| `arklint export --format <fmt>` | Export rules as an AI assistant instruction file |
| `arklint export --output <dir>` | Write exported file to a specific directory |
| `arklint learn --describe <text>` | Generate a rule from a plain-English description using AI |
| `arklint learn --provider <name>` | AI provider: `anthropic` or `openai` (required) |
| `arklint learn --append` | Append suggested rule to `.arklint.yml` without prompting |
| `arklint visualize` | Print a Mermaid diagram of your architecture rules |
| `arklint visualize -o <file>` | Write diagram to a file instead of stdout |
| `arklint watch` | Watch for file changes and re-run checks automatically |
| `arklint watch --strict` | Watch mode with strict severity |
| `arklint mcp` | Start the MCP server (stdio) for AI agent integration |
| `arklint --version` | Show version and exit |
