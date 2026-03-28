import tempfile
import textwrap
from pathlib import Path

from arklint.config import RuleConfig
from arklint.rules.pattern_ban import PatternBanRule


def make_file(content: str, suffix=".py") -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode="w")
    tmp.write(textwrap.dedent(content))
    tmp.close()
    return Path(tmp.name)


def make_rule(pattern: str, exclude=None, severity="warning") -> PatternBanRule:
    raw = {
        "id": "no-print",
        "type": "pattern-ban",
        "pattern": pattern,
        "severity": severity,
    }
    if exclude:
        raw["exclude"] = exclude
    cfg = RuleConfig(
        id="no-print",
        type="pattern-ban",
        description="No prints",
        severity=severity,
        raw=raw,
    )
    return PatternBanRule(cfg, root=Path("/"))


def test_detects_banned_pattern():
    f = make_file('print("hello")\n')
    rule = make_rule(r"print\(")
    violations = rule.check([f])
    assert len(violations) == 1
    assert violations[0].line == 1


def test_no_violation_on_clean_file():
    f = make_file('logging.info("hello")\n')
    rule = make_rule(r"print\(")
    violations = rule.check([f])
    assert violations == []


def test_multiple_violations():
    f = make_file('print("a")\nlogging.info("b")\nprint("c")\n')
    rule = make_rule(r"print\(")
    violations = rule.check([f])
    assert len(violations) == 2
