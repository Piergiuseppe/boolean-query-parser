from __future__ import annotations

from typing import Callable, Dict, Iterator

from .dates import BOUNDED_DATE_PATTERN, dates_in, parse_date, precision, truncate
from .numbers import BOUNDED_NUMBER_PATTERN, numbers_in, parse_number, standalone_number, to_number
from .operators import resolve_operator

ValueTest = Callable[[str], bool]


class ValueKind:
    """A family of values a query can compare, such as ``num`` or ``date``.

    ``scan`` finds the values in free text; ``pattern`` and ``standalone``
    let templates find the same values at a fixed place in the text.
    """

    name: str
    pattern: str

    def scan(self, text: str) -> Iterator[str]:
        raise NotImplementedError

    def standalone(self, text: str, start: int, end: int) -> bool:
        return True

    def bind(self, operator: str, threshold: str) -> ValueTest:
        raise NotImplementedError


class NumberKind(ValueKind):
    name = "num"
    pattern = BOUNDED_NUMBER_PATTERN

    def scan(self, text: str) -> Iterator[str]:
        return numbers_in(text)

    def standalone(self, text: str, start: int, end: int) -> bool:
        return standalone_number(text, start, end)

    def bind(self, operator: str, threshold: str) -> ValueTest:
        compare = resolve_operator(operator)
        target = parse_number(threshold)
        return lambda found: compare(to_number(found), target)


class DateKind(ValueKind):
    """Compares at the precision of the threshold: ``date:=2024-01-01`` matches any time that day."""

    name = "date"
    pattern = BOUNDED_DATE_PATTERN

    def scan(self, text: str) -> Iterator[str]:
        return dates_in(text)

    def bind(self, operator: str, threshold: str) -> ValueTest:
        compare = resolve_operator(operator)
        fields = precision(threshold)
        target = parse_date(threshold)

        def test(found: str) -> bool:
            # A day-level comparison only needs the date, even if the time is malformed.
            moment = parse_date(found[:10] if fields == 0 else found)
            return compare(truncate(moment, fields), target)

        return _ignoring_invalid(test)


def _ignoring_invalid(test: ValueTest) -> ValueTest:
    def guarded(found: str) -> bool:
        try:
            return test(found)
        except ValueError:
            return False

    return guarded


KINDS: Dict[str, ValueKind] = {kind.name: kind for kind in (NumberKind(), DateKind())}


def resolve_kind(name: str) -> ValueKind:
    try:
        return KINDS[name.lower()]
    except KeyError:
        raise ValueError(
            f"Unknown comparison type '{name}'. "
            f"Supported types: {', '.join(sorted(KINDS))}"
        ) from None
