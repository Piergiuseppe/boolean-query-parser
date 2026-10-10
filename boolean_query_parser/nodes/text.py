from __future__ import annotations

from .base import Node, Predicate


class TextNode(Node):
    __slots__ = ("value", "ignore_case")

    def __init__(self, value: str, ignore_case: bool = False) -> None:
        self.value = value
        self.ignore_case = ignore_case

    def compile(self) -> Predicate:
        if self.ignore_case:
            folded = self.value.casefold()
            return lambda text: folded in text.casefold()
        value = self.value
        return lambda text: value in text

    def __repr__(self) -> str:
        return f"Text({self.value!r})"
