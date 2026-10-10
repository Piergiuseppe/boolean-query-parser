from __future__ import annotations

from typing import Iterator

from ..explanation import Span
from ..values import resolve_kind
from .base import Leaf, TextPredicate


class ComparisonNode(Leaf):
    """Matches when any value of the given kind found in the text passes the comparison."""

    __slots__ = ("kind", "operator", "value", "_accepts")

    def __init__(self, kind: str, operator: str, value: str) -> None:
        self.kind = resolve_kind(kind)
        self.operator = operator
        self.value = value
        self._accepts = self.kind.bind(operator, value)

    def text_predicate(self) -> TextPredicate:
        scan = self.kind.scan
        accepts = self._accepts

        def predicate(text: str) -> bool:
            for start, end in scan(text):
                if accepts(text[start:end]):
                    return True
            return False

        return predicate

    def spans(self, text: str) -> Iterator[Span]:
        for start, end in self.kind.scan(text):
            if self._accepts(text[start:end]):
                yield start, end

    def __repr__(self) -> str:
        return f"Comparison({self.kind.name}:{self.operator}{self.value})"
