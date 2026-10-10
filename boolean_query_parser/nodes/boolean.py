from __future__ import annotations

from typing import Callable, Iterable, Sequence, Tuple

from ..explanation import Explanation
from .base import Node, Predicate, Subject


class NotNode(Node):
    __slots__ = ("child",)

    def __init__(self, child: Node) -> None:
        self.child = child

    def compile(self, records: bool = False) -> Predicate:
        child = self.child.compile(records)
        return lambda subject: not child(subject)

    def explain(self, subject: Subject) -> Explanation:
        child = self.child.explain(subject)
        return Explanation(self, not child.matched, children=(child,), negates=True)

    def label(self) -> str:
        return "NOT"

    def __repr__(self) -> str:
        return f"NOT({self.child!r})"


class _JunctionNode(Node):
    __slots__ = ("operands",)

    symbol = ""
    decide: Callable[[Iterable[bool]], bool] = all

    def __init__(self, *operands: Node) -> None:
        if len(operands) < 2:
            raise ValueError(f"{self.symbol} needs at least two operands")
        self.operands: Tuple[Node, ...] = tuple(self._flatten(operands))

    @classmethod
    def of(cls, operands: Sequence[Node]) -> Node:
        return operands[0] if len(operands) == 1 else cls(*operands)

    def _flatten(self, operands: Sequence[Node]):
        for operand in operands:
            if type(operand) is type(self):
                yield from operand.operands
            else:
                yield operand

    def compile(self, records: bool = False) -> Predicate:
        return self.combine(tuple(operand.compile(records) for operand in self.operands))

    @staticmethod
    def combine(predicates: Tuple[Predicate, ...]) -> Predicate:
        raise NotImplementedError

    def explain(self, subject: Subject) -> Explanation:
        children = tuple(operand.explain(subject) for operand in self.operands)
        matched = type(self).decide(child.matched for child in children)
        return Explanation(self, matched, children=children)

    def label(self) -> str:
        return self.symbol

    def __repr__(self) -> str:
        return "(" + f" {self.symbol} ".join(map(repr, self.operands)) + ")"


class AndNode(_JunctionNode):
    __slots__ = ()

    symbol = "AND"
    decide = all

    @staticmethod
    def combine(predicates: Tuple[Predicate, ...]) -> Predicate:
        if len(predicates) == 2:
            left, right = predicates
            return lambda subject: left(subject) and right(subject)

        def every(subject) -> bool:
            for predicate in predicates:
                if not predicate(subject):
                    return False
            return True

        return every


class OrNode(_JunctionNode):
    __slots__ = ()

    symbol = "OR"
    decide = any

    @staticmethod
    def combine(predicates: Tuple[Predicate, ...]) -> Predicate:
        if len(predicates) == 2:
            left, right = predicates
            return lambda subject: left(subject) or right(subject)

        def some(subject) -> bool:
            for predicate in predicates:
                if predicate(subject):
                    return True
            return False

        return some
