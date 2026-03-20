# Visualize

Generate a [Mermaid](https://mermaid.live) diagram of your architecture rules directly from `.arklint.yml`.

```bash
$ arklint visualize
```

## Output

The command prints a `flowchart LR` Mermaid block to stdout. You can paste it into any Markdown file or drop it into [mermaid.live](https://mermaid.live) to render it interactively.

For a three-layer setup the output looks like:

```
flowchart LR

    subgraph arch_layers ["Clean layers"]
        routes["routes\nroutes/**"]
        services["services\nservices/**"]
        repositories["repositories\nrepositories/**"]
        routes --> services
        routes -. blocked .-> repositories
        services --> repositories
        services -. blocked .-> routes
        repositories -. blocked .-> routes
        repositories -. blocked .-> services
    end
```

Solid arrows (`-->`) are **allowed** dependencies. Dashed arrows (`-. blocked .->`) are **blocked** ones.

## Write to a file

```bash
$ arklint visualize -o docs/architecture.md
✓ Diagram written to docs/architecture.md
```

You can then embed it in a Markdown page:

````markdown
```mermaid
flowchart LR
    ...
```
````

GitHub and most documentation platforms render Mermaid natively inside fenced code blocks.

## What gets visualised

| Rule type | Rendered as |
|-----------|-------------|
| `layer-boundary` | Directed graph with allowed/blocked edges per layer |
| `boundary` | Source directories → blocked import packages |
| `dependency` | "choose one" node connected to competing packages |
| `pattern-ban` | Not rendered (text-based, no graph structure) |
| `file-pattern` | Not rendered (text-based, no graph structure) |

## Options

| Flag | Description |
|------|-------------|
| `-o / --output <file>` | Write diagram to a file instead of stdout |
| `-c / --config <path>` | Use a config file from a custom path |
