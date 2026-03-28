# Installation

Arklint is available on **PyPI**, **npm**, and **NuGet**.

## Which method should I use?

| Feature | pip (PyPI) | npm | .NET (NuGet) |
|---------|:----------:|:---:|:------------:|
| `arklint check` | ✓ | ✓ | ✓ |
| `arklint watch` | ✓ | ✓ | ✓ |
| `arklint diff` | ✓ | ✓ | ✓ |
| `arklint visualize` | ✓ | ✓ | ✓ |
| `arklint learn` | ✓ | ✓ | ✓ |
| `arklint mcp` | ✓ (with `[mcp]` extra) | ✓ | ✓ |
| Python required | Yes (3.10+) | No | No |

All three methods run the same binary. Use **npm or .NET** if you are not in a Python project. Use **pip** if you want the MCP server extra or need to contribute.

## Python (PyPI)

Requires Python 3.10+.

```bash
$ pip install arklint
```

For MCP server support (AI agent integration):

```bash
$ pip install 'arklint[mcp]'
```

For AI-powered rule generation with `arklint learn` (already bundled in npm/.NET, only needed here):

```bash
$ pip install 'arklint[ai-anthropic]'   # Claude (Anthropic)
$ pip install 'arklint[ai-openai]'      # GPT-4o-mini (OpenAI)
```

> **Note:** The pip extras are named `ai-anthropic` and `ai-openai` - with the `ai-` prefix. `pip install arklint[anthropic]` will fail. The `--provider` flag uses just `anthropic` / `openai` (no prefix) - a different naming from the pip extras.

## Node.js (npm)

A thin wrapper that auto-downloads the platform-specific prebuilt binary on first run. **No Python required.**

```bash
# Run directly without installing
$ npx arklint check

# Or install globally
$ npm install -g arklint
$ arklint check
```

Supports Linux x64, macOS ARM64 (Apple Silicon), and Windows x64.

## .NET (NuGet)

A .NET global tool wrapper. Auto-downloads the prebuilt binary and caches it at `~/.arklint/bin/`. Requires .NET 8.0+.

```bash
$ dotnet tool install -g arklint
$ arklint check
```

> **Zero cloud dependency** - Arklint sends no data anywhere. Everything runs on your machine. The npm and .NET wrappers simply download a prebuilt binary and cache it locally.
