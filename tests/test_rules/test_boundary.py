from pathlib import Path
import tempfile
import textwrap

from arklint.config import RuleConfig
from arklint.rules.boundary import BoundaryRule


FIXTURES = Path(__file__).parent.parent / "fixtures"


def make_rule(root: Path, source: str, blocked: list[str]) -> BoundaryRule:
    raw = {
        "id": "no-db-in-routes",
        "type": "boundary",
        "source": source,
        "blocked_imports": blocked,
        "severity": "error",
    }
    cfg = RuleConfig(id="no-db-in-routes", type="boundary", description="No DB in routes", severity="error", raw=raw)
    return BoundaryRule(cfg, root=root)


def test_detects_blocked_import_in_routes():
    root = FIXTURES / "messy_project"
    files = list(root.rglob("*.py"))
    rule = make_rule(root, "routes/**", ["sqlalchemy", "psycopg2"])
    violations = rule.check(files)
    assert len(violations) >= 2


def test_no_violations_in_clean_project():
    root = FIXTURES / "clean_project"
    files = list(root.rglob("*.py"))
    rule = make_rule(root, "routes/**", ["sqlalchemy", "psycopg2"])
    violations = rule.check(files)
    assert violations == []
