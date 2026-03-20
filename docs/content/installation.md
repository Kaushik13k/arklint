# Installation

Arklint is available on **PyPI**, **npm**, and **NuGet**. All three install methods run the same binary.

## Python (PyPI)

The core CLI. Requires Python 3.10+. Includes all rule types, watch mode, diff mode, and JSON output.

```bash
$ pip install arklint
```

For MCP server support (AI agent integration), install with the optional extra:

```bash
$ pip install 'arklint[mcp]'
```

For AI-powered rule generation with `arklint learn`:

```bash
$ pip install 'arklint[ai-anthropic]'   # Claude (Anthropic)
$ pip install 'arklint[ai-openai]'      # GPT-4o-mini (OpenAI)
```

## Node.js (npm)

A thin wrapper that auto-downloads the platform-specific prebuilt binary from GitHub Releases on first run. **No Python needed** on the machine.

```bash
# Run directly without installing
$ npx arklint check

# Or install globally
$ npm install -g arklint
$ arklint check
```

Supports Linux x64, macOS ARM64 (Apple Silicon), and Windows x64.

## .NET (NuGet)

A .NET global tool wrapper. Also auto-downloads the prebuilt binary and caches it at `~/.arklint/bin/`. Requires .NET 8.0+.

```bash
$ dotnet tool install -g arklint
$ arklint check
```

> **Zero cloud dependency** — Arklint sends no data anywhere. Everything runs on your machine. The npm and .NET wrappers simply download a prebuilt binary and cache it locally.
