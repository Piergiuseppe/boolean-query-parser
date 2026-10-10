from __future__ import annotations

from typing import Sequence, Tuple

from .base import Node, Predicate


class NotNode(Node):
    __slots__ = ("child",)

    def __init__(self, child: Node) -> None:
        self.child = child

    def compile(self) -> Predicate:
        child = self.child.compile()
        return lambda text: not child(text)

    def __repr__(self) -> str:
        return f"NOT({self.child!r})"


class _JunctionNode(Node):
    __slots__ = ("operands",)

    symbol = ""

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

    def __repr__(self) -> str:
        return "(" + f" {self.symbol} ".join(map(repr, self.operands)) + ")"


class AndNode(_JunctionNode):
    __slots__ = ()

    symbol = "AND"

    def compile(self) -> Predicate:
        predicates = tuple(operand.compile() for operand in self.operands)
        if len(predicates) == 2:
            left, right = predicates
            return lambda text: left(text) and right(text)

        def every(text: str) -> bool:
            for predicate in predicates:
                if not predicate(text):
                    return False
            return True

        return every


class OrNode(_JunctionNode):
    __slots__ = ()

    symbol = "OR"

    def compile(self) -> Predicate:
        predicates = tuple(operand.compile() for operand in self.operands)
        if len(predicates) == 2:
            left, right = predicates
            return lambda text: left(text) or right(text)

        def some(text: str) -> bool:
            for predicate in predicates:
                if predicate(text):
                    return True
            return False

        return some
