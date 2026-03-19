from pathlib import Path

from arklint.config import RuleConfig
from arklint.rules.dependency import DependencyRule


FIXTURES = Path(__file__).parent.parent / "fixtures"


def make_rule(root: Path, allow_only_one_of: list[str]) -> DependencyRule:
    raw = {
        "id": "single-http-client",
        "type": "dependency",
        "allow_only_one_of": allow_only_one_of,
        "severity": "error",
    }
    cfg = RuleConfig(
        id="single-http-client", type="dependency",
        description="One HTTP client", severity="error", raw=raw
    )
    return DependencyRule(cfg, root=root)


def test_detects_multiple_http_clients():
    root = FIXTURES / "messy_project"
    files = list(root.rglob("*"))
    rule = make_rule(root, ["requests", "httpx", "aiohttp"])
    violations = rule.check(files)
    assert len(violations) == 1


def test_single_http_client_passes():
    root = FIXTURES / "clean_project"
    files = list(root.rglob("*"))
    rule = make_rule(root, ["requests", "httpx", "aiohttp"])
    violations = rule.check(files)
    assert violations == []
