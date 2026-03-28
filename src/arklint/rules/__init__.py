from .boundary import BoundaryRule
from .dependency import DependencyRule
from .file_pattern import FilePatternRule
from .layer_boundary import LayerBoundaryRule
from .pattern_ban import PatternBanRule

RULE_REGISTRY = {
    "boundary": BoundaryRule,
    "dependency": DependencyRule,
    "file-pattern": FilePatternRule,
    "pattern-ban": PatternBanRule,
    "layer-boundary": LayerBoundaryRule,
}

__all__ = [
    "BoundaryRule",
    "DependencyRule",
    "FilePatternRule",
    "PatternBanRule",
    "LayerBoundaryRule",
    "RULE_REGISTRY",
]
