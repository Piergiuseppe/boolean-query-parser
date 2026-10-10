from __future__ import annotations

import re
from datetime import datetime
from typing import Iterator

DATE_PATTERN = r"\d{4}[-/]\d{2}[-/]\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?(?!\d))?"
BOUNDED_DATE_PATTERN = rf"(?<!\d){DATE_PATTERN}(?!\d)"

_DATE = re.compile(DATE_PATTERN)
_LONGEST_DATE = len("2000-01-01T00:00:00")


def parse_date(raw: str) -> datetime:
    if _DATE.fullmatch(raw):
        try:
            return datetime.fromisoformat(raw.replace("/", "-").replace(" ", "T"))
        except ValueError:
            pass
    raise ValueError(
        f"Invalid date value: {raw!r}. "
        f"Expected format: YYYY-MM-DD or YYYY/MM/DD, optionally followed by THH:MM[:SS]"
    )


def precision(raw: str) -> int:
    """How many time fields ``raw`` spells out: 0 for a date, 1 for HH:MM, 2 for HH:MM:SS."""
    return raw.count(":")


def truncate(moment: datetime, fields: int) -> datetime:
    if fields == 0:
        return moment.replace(hour=0, minute=0, second=0, microsecond=0)
    if fields == 1:
        return moment.replace(second=0, microsecond=0)
    return moment


def dates_in(text: str) -> Iterator[str]:
    for match in _DATE.finditer(text):
        start, end = match.span()
        if (start and text[start - 1].isdigit()) or text[end:end + 1].isdigit():
            continue
        yield match.group()


def inside_date(text: str, start: int, end: int) -> bool:
    window = max(0, start - _LONGEST_DATE)
    return any(
        match.start() < end and match.end() > start
        for match in _DATE.finditer(text, window, end + _LONGEST_DATE)
    )
