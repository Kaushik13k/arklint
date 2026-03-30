"""Tests for scanner.py - file collection and default excludes."""

import tempfile
from pathlib import Path

import pathspec

from arklint.scanner import _DEFAULT_SPEC, DEFAULT_EXCLUDES, collect_files


class TestDefaultExcludes:
    def test_arklint_yml_is_excluded(self):
        assert ".arklint.yml" in DEFAULT_EXCLUDES

    def test_arklint_yaml_is_excluded(self):
        assert ".arklint.yaml" in DEFAULT_EXCLUDES


class TestDefaultSpec:
    def test_is_pathspec_instance(self):
        assert isinstance(_DEFAULT_SPEC, pathspec.PathSpec)

    def test_matches_git_dir(self):
        assert _DEFAULT_SPEC.match_file(".git/config")

    def test_matches_pycache(self):
        assert _DEFAULT_SPEC.match_file("__pycache__/foo.pyc")

    def test_does_not_match_source_file(self):
        assert not _DEFAULT_SPEC.match_file("src/app.py")


class TestCollectDiffFiles:
    def _make_project(self, files: dict[str, str]) -> Path:
        tmp = Path(tempfile.mkdtemp())
        for name, content in files.items():
            path = tmp / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        return tmp

    def test_returns_empty_list_outside_git_repo(self):
        from arklint.scanner import collect_diff_files

        root = self._make_project({"main.py": "x = 1"})
        # Not a git repo — git commands fail, result should be empty
        result = collect_diff_files(root, base="HEAD")
        assert result == []


class TestCollectFiles:
    def _make_project(self, files: dict[str, str]) -> Path:
        """Create a temp directory with the given filename→content mapping."""
        tmp = Path(tempfile.mkdtemp())
        for name, content in files.items():
            path = tmp / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        return tmp

    def test_arklint_yml_not_collected(self):
        root = self._make_project(
            {
                ".arklint.yml": "version: '1'\nrules: []",
                "main.py": "x = 1",
            }
        )
        files = collect_files(root)
        names = [f.name for f in files]
        assert ".arklint.yml" not in names
        assert "main.py" in names

    def test_arklint_yaml_not_collected(self):
        root = self._make_project(
            {
                ".arklint.yaml": "version: '1'\nrules: []",
                "main.py": "x = 1",
            }
        )
        files = collect_files(root)
        names = [f.name for f in files]
        assert ".arklint.yaml" not in names

    def test_source_files_are_collected(self):
        root = self._make_project(
            {
                "src/app.py": "print('hello')",
                "src/utils.py": "pass",
            }
        )
        files = collect_files(root)
        names = [f.name for f in files]
        assert "app.py" in names
        assert "utils.py" in names

    def test_git_dir_not_collected(self):
        root = self._make_project(
            {
                ".git/config": "[core]",
                "main.py": "x = 1",
            }
        )
        files = collect_files(root)
        paths = [str(f) for f in files]
        assert not any(".git" in p for p in paths)

    def test_pycache_not_collected(self):
        root = self._make_project(
            {
                "__pycache__/main.cpython-312.pyc": "",
                "main.py": "x = 1",
            }
        )
        files = collect_files(root)
        paths = [str(f) for f in files]
        assert not any("__pycache__" in p for p in paths)
