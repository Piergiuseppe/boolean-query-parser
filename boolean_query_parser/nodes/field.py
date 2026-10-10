from __future__ import annotations

from ..exceptions import QueryError
from ..explanation import Explanation
from ..records import Record
from .base import Node, Predicate, Subject


class FieldNode(Node):
    """``name:term`` — the term must match the value of one field of a record."""

    __slots__ = ("name", "child")

    def __init__(self, name: str, child: Node) -> None:
        self.name = name
        self.child = child

    def compile(self, records: bool = False) -> Predicate:
        if not records:
            raise self._needs_records()
        child = self.child.compile()
        name = self.name

        def predicate(record: Record) -> bool:
            value = record.field(name)
            return value is not None and child(value)

        return predicate

    def explain(self, subject: Subject) -> Explanation:
        if not isinstance(subject, Record):
            raise self._needs_records()
        value = subject.field(self.name)
        if value is None:
            return Explanation(self, False, field=self.name)
        child = self.child.explain(value)
        return Explanation(self, child.matched, children=(child,), field=self.name)

    def _needs_records(self) -> QueryError:
        return QueryError(
            f"'{self.name}:' scopes a term to a field, so the query only applies to "
            f"mappings, not plain text. For a comparison write an operator, e.g. num:=5"
        )

    def label(self) -> str:
        return f"{self.name}:"

    def __repr__(self) -> str:
        return f"Field({self.name!r}, {self.child!r})"
