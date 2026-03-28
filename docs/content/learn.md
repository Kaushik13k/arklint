# AI Rule Generation

Generate a valid `.arklint.yml` rule from a plain-English description using AI.

```bash
$ arklint learn --describe "no raw SQL queries in route handlers" --provider anthropic
$ arklint learn --describe "no raw SQL queries in route handlers" --provider openai
```

Arklint prompts the AI with your description and the full rule schema. The AI returns a ready-to-use YAML rule block. You can review it and optionally append it to your `.arklint.yml`.

The `anthropic` and `openai` SDKs are bundled in the prebuilt binary, so `arklint learn` works out of the box regardless of whether you installed via pip, npm, or .NET. All you need is an API key.

## pip install - optional extras

If you installed via pip, install the AI extra for your provider:

```bash
$ pip install 'arklint[ai-anthropic]'   # Claude (Anthropic)
$ pip install 'arklint[ai-openai]'      # GPT-4o-mini (OpenAI)
```

> **Note:** The pip extras are named `ai-anthropic` and `ai-openai` - with the `ai-` prefix. `pip install arklint[anthropic]` will fail. The `--provider` flag uses just `anthropic` or `openai` (no prefix) - a different naming from the pip extras.

## Options

| Flag | Description |
|------|-------------|
| `--describe` / `-d` | Plain-English description of the rule (required) |
| `--provider` / `-p` | AI provider: `anthropic` or `openai` (required) |
| `--api-key` | API key for the provider. Falls back to `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` |
| `--append` / `-a` | Append the rule to `.arklint.yml` without confirmation prompt |
| `--config` / `-c` | Path to `.arklint.yml`. Auto-discovered if omitted |

## Example session

```bash
$ arklint learn --describe "services must not import from routes" --provider anthropic

Generating rule via anthropic…

Suggested rule:

- id: no-routes-in-services
  type: boundary
  description: Services must not import from route handlers
  source: "services/**"
  blocked_imports:
    - "routes"
  severity: error

Append this rule to .arklint.yml? [y/N]: y
✓ Rule appended to /my-project/.arklint.yml
  Run arklint validate to confirm the config is valid.
```

> Your API key is never stored by Arklint. It is read from the environment variable or `--api-key` flag and passed directly to the provider's SDK at runtime.
