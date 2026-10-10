from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, Iterator, Pattern, Tuple

Span = Tuple[int, int]

_AMOUNT = r"\d+(?:\.\d+)?"

# Fractions keep conversions exact, so dur:=1.1ms matches "1100us".
DURATION_UNITS: Dict[str, Fraction] = {
    "us": Fraction(1, 10**6), "µs": Fraction(1, 10**6), "μs": Fraction(1, 10**6),
    "ms": Fraction(1, 1000),
    "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    "m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
    "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
    "d": 86400, "day": 86400, "days": 86400,
}

# Decimal multiples for kB/MB/..., binary ones for KiB/MiB/...; case is ignored.
SIZE_UNITS: Dict[str, int] = {
    "b": 1, "byte": 1, "bytes": 1,
    "kb": 10**3, "mb": 10**6, "gb": 10**9, "tb": 10**12,
    "kib": 2**10, "mib": 2**20, "gib": 2**30, "tib": 2**40,
}


def _alternation(units: Dict[str, object]) -> str:
    return "|".join(re.escape(unit) for unit in sorted(units, key=len, reverse=True))


DURATION_PATTERN = rf"(?<![\w.]){_AMOUNT} ?(?:{_alternation(DURATION_UNITS)})(?!\w)"
SIZE_PATTERN = rf"(?<![\w.]){_AMOUNT} ?(?i:{_alternation(SIZE_UNITS)})(?!\w)"

_DURATION = re.compile(DURATION_PATTERN)
_SIZE = re.compile(SIZE_PATTERN)
_SPLIT = re.compile(rf"({_AMOUNT}) ?(\S+)")


def parse_duration(raw: str) -> Fraction:
    return _parse(raw, _DURATION, DURATION_UNITS, case_sensitive=True, example="dur:<1.5s or dur:>200ms")


def parse_size(raw: str) -> Fraction:
    return _parse(raw, _SIZE, SIZE_UNITS, case_sensitive=False, example="size:>10MB or size:<=512KiB")


def durations_in(text: str) -> Iterator[Span]:
    for match in _DURATION.finditer(text):
        yield match.span()


def sizes_in(text: str) -> Iterator[Span]:
    for match in _SIZE.finditer(text):
        yield match.span()


def _parse(raw: str, pattern: Pattern[str], units, case_sensitive: bool, example: str) -> Fraction:
    parts = _SPLIT.fullmatch(raw) if pattern.fullmatch(raw) else None
    if parts is None:
        raise ValueError(f"Invalid quantity: {raw!r}. Expected an amount with a unit, e.g. {example}")
    amount, unit = parts.groups()
    return Fraction(amount) * units[unit if case_sensitive else unit.lower()]
