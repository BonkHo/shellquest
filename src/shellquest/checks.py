"""Answer normalization helpers. Pure functions, no I/O."""

import re
from decimal import Decimal

_NUMBER = re.compile(r"-?\d+(\.\d+)?")


def last_line(text: str) -> str:
    """The last non-empty line, so `ls -A && cat file` piped in still works."""
    for line in reversed(text.splitlines()):
        if line.strip():
            return line
    return ""


def normalize(text: str) -> str:
    """Last line, stripped of whitespace (macOS `wc -l` pads) and surrounding quotes, lowercased."""
    line = last_line(text).strip()
    if len(line) >= 2 and line[0] == line[-1] and line[0] in "'\"":
        line = line[1:-1].strip()
    return line.casefold()


def matches_text(given: str, expected: str) -> bool:
    return normalize(given) == normalize(expected)


def _as_number(text: str) -> Decimal | None:
    cleaned = normalize(text).removeprefix("$")
    if _NUMBER.fullmatch(cleaned):
        return Decimal(cleaned)
    return None


def matches_number(given: str, expected: str) -> bool:
    """Compare numerically, ignoring `$` and trailing zeros (187.50 == $187.5)."""
    # Decimal, not float, so 187.50 vs 187.5 is an exact comparison.
    given_number, expected_number = _as_number(given), _as_number(expected)
    return given_number is not None and given_number == expected_number


def matches_file(given: str, expected: str) -> bool:
    """Accept the basename or any path that ends in it (`sync.py`, `src/pantry/sync.py`)."""
    given_path, expected_name = normalize(given), normalize(expected)
    return given_path == expected_name or given_path.endswith(f"/{expected_name}")
