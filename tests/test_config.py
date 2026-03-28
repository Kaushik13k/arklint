import tempfile
import textwrap
from pathlib import Path

import pytest

from arklint.config import ConfigError, load_config


def write_config(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".yml", delete=False, mode="w")
    tmp.write(textwrap.dedent(content))
    tmp.close()
    return Path(tmp.name)


def test_load_valid_config():
    p = write_config(
        """
        version: "1"
        rules:
          - id: no-print
            type: pattern-ban
            description: No print statements
            pattern: "print\\\\("
            severity: warning
    """
    )
    cfg = load_config(p)
    assert cfg.version == "1"
    assert len(cfg.rules) == 1
    assert cfg.rules[0].id == "no-print"
    assert cfg.rules[0].type == "pattern-ban"
    assert cfg.rules[0].severity == "warning"


def test_missing_id_raises():
    p = write_config(
        """
        version: "1"
        rules:
          - type: pattern-ban
            pattern: "print\\\\("
    """
    )
    with pytest.raises(ConfigError, match="missing required field 'id'"):
        load_config(p)


def test_unknown_type_raises():
    p = write_config(
        """
        version: "1"
        rules:
          - id: test-rule
            type: unknown-type
    """
    )
    with pytest.raises(ConfigError, match="unknown type"):
        load_config(p)


def test_invalid_severity_raises():
    p = write_config(
        """
        version: "1"
        rules:
          - id: test-rule
            type: pattern-ban
            severity: critical
    """
    )
    with pytest.raises(ConfigError, match="invalid severity"):
        load_config(p)
