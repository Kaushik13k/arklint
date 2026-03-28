"""Tests for scanner.py - file collection and default excludes."""
import tempfile
from pathlib import Path

from arklint.scanner import collect_files, DEFAULT_EXCLUDES


class TestDefaultExcludes:
    def test_arklint_yml_is_excluded(self):
        assert ".arklint.yml" in DEFAULT_EXCLUDES

    def test_arklint_yaml_is_excluded(self):
        assert ".arklint.yaml" in DEFAULT_EXCLUDES


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
        root = self._make_project({
            ".arklint.yml": "version: '1'\nrules: []",
            "main.py": "x = 1",
        })
        files = collect_files(root)
        names = [f.name for f in files]
        assert ".arklint.yml" not in names
        assert "main.py" in names

    def test_arklint_yaml_not_collected(self):
        root = self._make_project({
            ".arklint.yaml": "version: '1'\nrules: []",
            "main.py": "x = 1",
        })
        files = collect_files(root)
        names = [f.name for f in files]
        assert ".arklint.yaml" not in names

    def test_source_files_are_collected(self):
        root = self._make_project({
            "src/app.py": "print('hello')",
            "src/utils.py": "pass",
        })
        files = collect_files(root)
        names = [f.name for f in files]
        assert "app.py" in names
        assert "utils.py" in names

    def test_git_dir_not_collected(self):
        root = self._make_project({
            ".git/config": "[core]",
            "main.py": "x = 1",
        })
        files = collect_files(root)
        paths = [str(f) for f in files]
        assert not any(".git" in p for p in paths)

    def test_pycache_not_collected(self):
        root = self._make_project({
            "__pycache__/main.cpython-312.pyc": "",
            "main.py": "x = 1",
        })
        files = collect_files(root)
        paths = [str(f) for f in files]
        assert not any("__pycache__" in p for p in paths)
