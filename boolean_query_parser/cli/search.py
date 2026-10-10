from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import IO, Callable, Iterator, Optional

from ..explanation import Explanation
from ..nodes import Node
from ..records import Record


@dataclass(frozen=True)
class Line:
    number: int
    text: str
    explanation: Optional[Explanation] = None


class LineSearch:
    """Selects the lines of a stream that match a query, like grep."""

    def __init__(self, query: Node, *, records: bool, invert: bool, explain: bool) -> None:
        self._query = query
        self._records = records
        self._invert = invert
        self._explain = explain
        self._predicate = query.compile(records=records)

    def selected(self, stream: IO[str], skip: Callable[[str], None]) -> Iterator[Line]:
        """Yield the selected lines; lines that cannot be read as records go to ``skip``."""
        for number, raw in enumerate(stream, start=1):
            text = raw.rstrip("\r\n")
            subject = self._subject(text, number, skip)
            if subject is None or self._predicate(subject) is self._invert:
                continue
            explanation = self._query.explain(subject) if self._explain else None
            yield Line(number, text, explanation)

    def _subject(self, text: str, number: int, skip: Callable[[str], None]):
        if not self._records:
            return text
        try:
            data = json.loads(text)
        except ValueError as error:
            skip(f"line {number} is not valid JSON: {error}")
            return None
        if not isinstance(data, Mapping):
            skip(f"line {number} is a JSON {type(data).__name__}, not an object")
            return None
        return Record(data)
