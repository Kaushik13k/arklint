"""AI-powered rule generation.

Supports multiple providers:
  - anthropic  (default) - Claude Haiku via ANTHROPIC_API_KEY
  - openai               - GPT-4o-mini via OPENAI_API_KEY

Usage
-----
Call :func:`suggest_rule` with a plain-English description of what you want
to enforce and it returns a YAML snippet ready to paste into .arklint.yml.
"""

from __future__ import annotations

import os
import textwrap

SUPPORTED_PROVIDERS = ("anthropic", "openai")

_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
_OPENAI_MODEL = "gpt-4o-mini"
_MAX_TOKENS = 512

SYSTEM_PROMPT = textwrap.dedent(
    """\
    You are an expert software architect helping users define architectural
    rules for their codebase using the arklint tool.

    Arklint rules are defined in YAML. The supported rule types and their
    required fields are:

    1. pattern-ban - ban a regex pattern in file contents
       required: id, type, description, pattern, severity

    2. boundary - prevent one module group from importing another
       required: id, type, description, from_modules (list), banned_imports (list), severity

    3. dependency - enforce that a module only imports from an allowed list
       required: id, type, description, module_pattern, allowed_imports (list), severity

    4. file-pattern - enforce naming conventions on files in a directory
       required: id, type, description, directory, pattern, severity

    5. layer-boundary - enforce strict layer ordering (e.g. routes→services→repos)
       required: id, type, description, layers (list of module name strings), severity

    severity must be "error" or "warning".

    When the user describes what they want to enforce, output EXACTLY one YAML
    rule block - nothing else. No explanation, no markdown fences, no comments.
    The block must start with "- id:" and be valid YAML.

    Example output:
    - id: no-print-statements
      type: pattern-ban
      description: Use structured logging instead of print()
      pattern: 'print\\('
      severity: warning
"""
)


def suggest_rule(
    description: str,
    provider: str = "anthropic",
    api_key: str | None = None,
) -> str:
    """Call an AI provider and return a YAML rule snippet.

    Parameters
    ----------
    description:
        Plain-English description of the rule to generate.
    provider:
        AI backend to use: ``"anthropic"`` (default) or ``"openai"``.
    api_key:
        API key for the chosen provider. Falls back to the relevant env var:
        ``ANTHROPIC_API_KEY`` or ``OPENAI_API_KEY``.

    Returns
    -------
    str
        A YAML rule block starting with ``- id:``.

    Raises
    ------
    ImportError
        If the required SDK package is not installed.
    ValueError
        If no API key is available or provider is unknown.
    RuntimeError
        If the API call fails or returns an unexpected response.
    """
    if provider == "anthropic":
        return _suggest_anthropic(description, api_key)
    if provider == "openai":
        return _suggest_openai(description, api_key)
    raise ValueError(
        f"Unknown provider: {provider!r}. Choose from: {', '.join(SUPPORTED_PROVIDERS)}"
    )


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------


def _validate_response(raw: str, provider: str) -> str:
    raw = raw.strip()
    if not raw.startswith("- id:"):
        raise RuntimeError(f"Unexpected response from {provider} API:\n{raw}")
    return raw


def _suggest_anthropic(description: str, api_key: str | None) -> str:
    try:
        import anthropic
    except ImportError as exc:
        raise ImportError(
            "The 'anthropic' package is required for --provider anthropic.\n"
            "Install it with: pip install 'arklint[ai-anthropic]'"
        ) from exc

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "No Anthropic API key found. "
            "Set the ANTHROPIC_API_KEY environment variable or pass --api-key."
        )

    client = anthropic.Anthropic(api_key=key)
    message = client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": description}],
    )
    return _validate_response(message.content[0].text, "Anthropic")


def _suggest_openai(description: str, api_key: str | None) -> str:
    try:
        import openai
    except ImportError as exc:
        raise ImportError(
            "The 'openai' package is required for --provider openai.\n"
            "Install it with: pip install 'arklint[ai-openai]'"
        ) from exc

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError(
            "No OpenAI API key found. "
            "Set the OPENAI_API_KEY environment variable or pass --api-key."
        )

    client = openai.OpenAI(api_key=key)
    response = client.chat.completions.create(
        model=_OPENAI_MODEL,
        max_tokens=_MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": description},
        ],
    )
    return _validate_response(response.choices[0].message.content, "OpenAI")
