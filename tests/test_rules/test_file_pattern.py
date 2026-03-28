"""Tests for FilePatternRule."""

from __future__ import annotations

import textwrap
from pathlib import Path

from arklint.config import RuleConfig
from arklint.rules.file_pattern import FilePatternRule


def _make_rule(pattern: str, allowed_in: str | list[str], root: Path) -> FilePatternRule:
    raw = {
        "id": "test/file-pattern",
        "type": "file-pattern",
        "description": "Test rule",
        "pattern": pattern,
        "allowed_in": allowed_in,
        "severity": "warning",
    }
    cfg = RuleConfig(
        id="test/file-pattern",
        type="file-pattern",
        description="Test rule",
        severity="warning",
        raw=raw,
    )
    return FilePatternRule(config=cfg, root=root)


def _write(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content))
    return p


# ── basic detection ───────────────────────────────────────────────────────────


class TestFilePatternDetection:
    def test_pattern_in_disallowed_dir_reports_violation(self, tmp_path):
        f = _write(tmp_path, "routes/user.py", "class UserModel(Base): pass\n")
        rule = _make_rule(r"class\s+\w+Model", "models/**", tmp_path)
        violations = rule.check([f])
        assert len(violations) == 1
        assert "routes/user.py" in violations[0].file.as_posix()

    def test_pattern_in_allowed_dir_no_violation(self, tmp_path):
        f = _write(tmp_path, "models/user.py", "class UserModel(Base): pass\n")
        rule = _make_rule(r"class\s+\w+Model", "models/**", tmp_path)
        assert rule.check([f]) == []

    def test_no_pattern_match_no_violation(self, tmp_path):
        f = _write(tmp_path, "routes/user.py", "def get_user(): pass\n")
        rule = _make_rule(r"class\s+\w+Model", "models/**", tmp_path)
        assert rule.check([f]) == []

    def test_multiple_violations_in_one_file(self, tmp_path):
        f = _write(
            tmp_path,
            "routes/user.py",
            ("class UserModel(Base): pass\nclass OrderModel(Base): pass\n"),
        )
        rule = _make_rule(r"class\s+\w+Model", "models/**", tmp_path)
        violations = rule.check([f])
        assert len(violations) == 2

    def test_correct_line_number_reported(self, tmp_path):
        f = _write(
            tmp_path,
            "services/x.py",
            ("# line 1\n# line 2\nclass FooModel(Base): pass\n"),
        )
        rule = _make_rule(r"class\s+\w+Model", "models/**", tmp_path)
        violations = rule.check([f])
        assert violations[0].line == 3


# ── allowed_in variants ───────────────────────────────────────────────────────


class TestAllowedInVariants:
    def test_allowed_in_as_string(self, tmp_path):
        f = _write(tmp_path, "models/user.py", "class UserModel(Base): pass\n")
        rule = _make_rule(r"class\s+\w+Model", "models/**", tmp_path)
        assert rule.check([f]) == []

    def test_allowed_in_as_list(self, tmp_path):
        f = _write(tmp_path, "schemas/user.py", "class UserModel(Base): pass\n")
        rule = _make_rule(r"class\s+\w+Model", ["models/**", "schemas/**"], tmp_path)
        assert rule.check([f]) == []

    def test_allowed_in_list_second_path_matches(self, tmp_path):
        f = _write(tmp_path, "schemas/user.py", "class UserModel(Base): pass\n")
        rule = _make_rule(r"class\s+\w+Model", ["models/**", "schemas/**"], tmp_path)
        assert rule.check([f]) == []

    def test_disallowed_when_not_in_any_allowed(self, tmp_path):
        f = _write(tmp_path, "routes/user.py", "class UserModel(Base): pass\n")
        rule = _make_rule(r"class\s+\w+Model", ["models/**", "schemas/**"], tmp_path)
        assert len(rule.check([f])) == 1


# ── edge cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_files_list(self, tmp_path):
        rule = _make_rule(r"class\s+\w+Model", "models/**", tmp_path)
        assert rule.check([]) == []

    def test_missing_pattern_returns_empty(self, tmp_path):
        f = _write(tmp_path, "routes/user.py", "class UserModel(Base): pass\n")
        raw = {
            "id": "test/file-pattern",
            "type": "file-pattern",
            "description": "Test",
            "allowed_in": "models/**",
            "severity": "warning",
        }
        cfg = RuleConfig(
            id="test/file-pattern",
            type="file-pattern",
            description="Test",
            severity="warning",
            raw=raw,
        )
        rule = FilePatternRule(config=cfg, root=tmp_path)
        assert rule.check([f]) == []

    def test_missing_allowed_in_returns_empty(self, tmp_path):
        f = _write(tmp_path, "routes/user.py", "class UserModel(Base): pass\n")
        raw = {
            "id": "test/file-pattern",
            "type": "file-pattern",
            "description": "Test",
            "pattern": r"class\s+\w+Model",
            "severity": "warning",
        }
        cfg = RuleConfig(
            id="test/file-pattern",
            type="file-pattern",
            description="Test",
            severity="warning",
            raw=raw,
        )
        rule = FilePatternRule(config=cfg, root=tmp_path)
        assert rule.check([f]) == []

    def test_violation_message_contains_allowed_paths(self, tmp_path):
        f = _write(tmp_path, "routes/user.py", "class UserModel(Base): pass\n")
        rule = _make_rule(r"class\s+\w+Model", "models/**", tmp_path)
        violations = rule.check([f])
        assert "models/**" in violations[0].message

    def test_nested_allowed_path(self, tmp_path):
        f = _write(tmp_path, "src/models/deep/user.py", "class UserModel(Base): pass\n")
        rule = _make_rule(r"class\s+\w+Model", "**/models/**", tmp_path)
        assert rule.check([f]) == []
