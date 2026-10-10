from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any, Optional

_MISSING = object()


class Record:
    """A mapping seen through a query: ``field()`` for scoped terms, ``text`` for the rest.

    Field names may be dotted to reach into nested mappings, so ``user.name``
    reads ``{"user": {"name": ...}}`` unless a literal ``"user.name"`` key exists.
    """

    __slots__ = ("data", "_text")

    def __init__(self, data: Mapping[str, Any]) -> None:
        self.data = data

    @property
    def text(self) -> str:
        try:
            return self._text
        except AttributeError:
            self._text = flatten(self.data)
            return self._text

    def field(self, name: str) -> Optional[str]:
        value = _lookup(self.data, name)
        return None if value is _MISSING else flatten(value)


def flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Mapping):
        return "\n".join(flatten(item) for item in value.values())
    if isinstance(value, (list, tuple, set, frozenset)):
        return "\n".join(flatten(item) for item in value)
    if isinstance(value, float):
        # Avoid scientific notation, which would read as several numbers ("1e-07" -> 1 and 7).
        return format(Decimal(repr(value)), "f")
    return str(value)


def _lookup(data: Mapping[str, Any], name: str) -> Any:
    if name in data:
        return data[name]
    current: Any = data
    for part in name.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return _MISSING
        current = current[part]
    return current
