# Contributing

Arklint is open source and welcomes contributions. Every change goes through a pull request.

## Dev setup

```bash
$ git clone https://github.com/Kaushik13k/arklint
$ cd arklint
$ python -m venv .venv && source .venv/bin/activate
$ pip install -e ".[dev]"
$ pytest -v
```

Ground rules: every PR needs CODEOWNER approval, every source change needs a test, and all CI checks must pass. See [CONTRIBUTING.md](https://github.com/Kaushik13k/arklint/blob/main/CONTRIBUTING.md) for the full guide.
