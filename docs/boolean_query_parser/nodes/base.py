from __future__ import annotations

from typing import Callable

Predicate = Callable[[str], bool]


class Node:
    __slots__ = ("_predicate",)

    def compile(self) -> Predicate:
        raise NotImplementedError

    def _compile(self) -> Predicate:
        return self.compile()

    def evaluate(self, text: str) -> bool:
        try:
            predicate = self._predicate
        except AttributeError:
            predicate = self._predicate = self.compile()
        return predicate(text)
