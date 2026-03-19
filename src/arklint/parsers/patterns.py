from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PatternMatch:
    line_number: int
    line: str
    match: str


def scan_pattern(path: Path, pattern: str) -> list[PatternMatch]:
    """Find all lines in a file matching the regex pattern."""
    try:
        content = path.read_text(errors="ignore")
    except OSError:
        return []

    try:
        compiled = re.compile(pattern)
    except re.error:
        return []

    matches = []
    for i, line in enumerate(content.splitlines(), start=1):
        m = compiled.search(line)
        if m:
            matches.append(PatternMatch(line_number=i, line=line.strip(), match=m.group(0)))
    return matches
