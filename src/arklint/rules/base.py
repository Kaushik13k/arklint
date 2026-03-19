"""Base types for Arklint rules.

Every rule must satisfy the ``Rule`` Protocol — implement ``check()`` and
nothing else is required.  The ``BaseRule`` convenience class handles the
boilerplate (config access, root path, violation factory).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from arklint.config import RuleConfig


@dataclass(slots=True, frozen=True)
class Violation:
    """A single rule violation found in the codebase."""

    rule_id: str
    severity: str       # "error" | "warning"
    file: Path
    line: int | None    # None when not applicable (e.g. dependency-level check)
    message: str


@runtime_checkable
class Rule(Protocol):
    """Structural protocol every rule must satisfy.

    Arklint discovers rules via :data:`arklint.rules.RULE_REGISTRY`.  Any
    class registered there must be callable as ``cls(config, root)`` and
    expose a ``check`` method with this exact signature.
    """

    def check(self, files: list[Path]) -> list[Violation]:
        """Evaluate the rule against *files* and return all violations found."""
        ...


class BaseRule:
    """Shared scaffolding for concrete rule implementations.

    Subclass this, override :meth:`check`, and register in ``RULE_REGISTRY``.
    """

    __slots__ = ("config", "root")

    def __init__(self, config: "RuleConfig", root: Path) -> None:
        self.config = config
        self.root = root

    def check(self, files: list[Path]) -> list[Violation]:  # pragma: no cover
        raise NotImplementedError(f"{type(self).__name__}.check() not implemented")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _violation(self, file: Path, line: int | None, message: str) -> Violation:
        return Violation(
            rule_id=self.config.id,
            severity=self.config.severity,
            file=file,
            line=line,
            message=message,
        )

    def _rel(self, path: Path) -> str:
        """Return *path* relative to ``self.root``, falling back to the absolute path."""
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)
