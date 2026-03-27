# Language Support

Arklint is language-agnostic. Import extraction and dependency file parsing are built in for the most common languages and package managers — no plugins or configuration needed.

## Import extraction

Arklint reads import statements from source files to enforce `boundary` and `layer-boundary` rules.

| Language | File extensions | Import syntax detected |
|----------|----------------|------------------------|
| Python | `.py` | `import x`, `from x import y` |
| JavaScript | `.js`, `.mjs`, `.cjs` | `import`, `require()` |
| TypeScript | `.ts`, `.tsx` | `import`, `require()` |
| Go | `.go` | `import "pkg"`, `import ( ... )` |
| Ruby | `.rb` | `require`, `require_relative` |
| Rust | `.rs` | `use crate::`, `extern crate` |
| Java | `.java` | `import com.example.Class` |
| C# | `.cs` | `using Namespace` |
| PHP | `.php` | `use`, `require`, `include` |

## Dependency file parsing

Arklint reads dependency files to enforce `dependency` rules (e.g. "keep only one HTTP client").

| Package manager | File |
|-----------------|------|
| Python (pip) | `requirements.txt` |
| Python (modern) | `pyproject.toml` |
| Node.js | `package.json` |
| Go | `go.mod` |
| Rust | `Cargo.toml` |
| Ruby | `Gemfile` |

## Language detection

Arklint detects language from file extension automatically. No configuration is needed — rules based on file paths (like `source: "routes/**"`) match regardless of the file's language.

> **Missing a language?** Open an issue or pull request on [GitHub](https://github.com/Kaushik13k/ark-lint). Adding a new parser is straightforward — see [Contributing](#contributing).
