from __future__ import annotations

from ..values import resolve_kind
from .base import Node, Predicate


class ComparisonNode(Node):
    """Matches when any value of the given kind found in the text passes the comparison."""

    __slots__ = ("kind", "operator", "value", "_accepts")

    def __init__(self, kind: str, operator: str, value: str) -> None:
        self.kind = resolve_kind(kind)
        self.operator = operator
        self.value = value
        self._accepts = self.kind.bind(operator, value)

    def compile(self) -> Predicate:
        scan = self.kind.scan
        accepts = self._accepts

        def predicate(text: str) -> bool:
            for found in scan(text):
                if accepts(found):
                    return True
            return False

        return predicate

    def __repr__(self) -> str:
        return f"Comparison({self.kind.name}:{self.operator}{self.value})"
