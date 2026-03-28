"""Tests for the __main__ module (python -m arklint entry point)."""

import subprocess
import sys


def test_python_m_arklint_version():
    """python -m arklint --version should print the version and exit 0."""
    result = subprocess.run(
        [sys.executable, "-m", "arklint", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "arklint v" in result.stdout


def test_python_m_arklint_help():
    """python -m arklint --help should exit 0."""
    result = subprocess.run(
        [sys.executable, "-m", "arklint", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
