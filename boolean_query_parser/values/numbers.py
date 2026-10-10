from __future__ import annotations

import re
from typing import Iterator, Union

from .dates import DATE_PATTERN, inside_date

Number = Union[int, float]

NUMBER_PATTERN = r"-?\d+(?:\.\d+)?"

# For templates, where the surrounding literal text keeps the scan fast. A digit
# may not follow another digit, a dot, or a minus that is itself a sign.
BOUNDED_NUMBER_PATTERN = r"(?:(?<![\w.])-|(?<![\d.])(?<!(?<![\w.])-))\d+(?:\.\d+)?(?!\d)"

_SCANNER = re.compile(f"(?P<date>{DATE_PATTERN})|(?P<number>{NUMBER_PATTERN})")
_DATE_SEPARATORS_BEFORE = ("-", "/", ":", "T")
_DATE_SEPARATORS_AFTER = ("-", "/", ":")
_THRESHOLD = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)")


def parse_number(raw: str) -> Number:
    if not _THRESHOLD.fullmatch(raw):
        raise ValueError(f"Invalid numeric value: {raw!r}")
    return to_number(raw)


def to_number(found: str) -> Number:
    if "." not in found:
        try:
            return int(found)
        except ValueError:
            pass
    return float(found)


def numbers_in(text: str) -> Iterator[str]:
    """Yield the numbers in ``text`` that are not part of a date or a dotted run like ``1.2.3``.

    A minus right after a word character is a hyphen, not a sign, so
    ``"pages 3-7"`` yields 3 and 7.
    """
    for match in _SCANNER.finditer(text):
        found = match.group("number")
        if found is None:
            continue
        start = match.start()
        before = text[start - 1] if start else ""
        if before == ".":
            continue
        if found[0] == "-" and (before.isalnum() or before == "_"):
            found = found[1:]
        yield found


def standalone_number(text: str, start: int, end: int) -> bool:
    # Every number inside a date or time touches one of these separators.
    before = text[start - 1:start]
    after = text[end:end + 1]
    if before not in _DATE_SEPARATORS_BEFORE and after not in _DATE_SEPARATORS_AFTER:
        return True
    return not inside_date(text, start, end)
