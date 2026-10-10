from __future__ import annotations

from typing import Any, Callable, Iterator, Union

from ..explanation import Explanation, Span
from ..records import Record

Predicate = Callable[[Any], bool]
TextPredicate = Callable[[str], bool]
Subject = Union[str, Record]


class Node:
    """A query tree node.

    ``compile()`` builds a predicate over strings, ``compile(records=True)`` one
    over :class:`Record` objects; ``explain()`` reports why a subject matched.
    """

    __slots__ = ("_predicate", "_record_predicate")

    def compile(self, records: bool = False) -> Predicate:
        raise NotImplementedError

    def explain(self, subject: Subject) -> Explanation:
        raise NotImplementedError

    def label(self) -> str:
        return repr(self)

    def _compile(self) -> Predicate:
        return self.compile()

    def evaluate(self, text: str) -> bool:
        try:
            predicate = self._predicate
        except AttributeError:
            predicate = self._predicate = self.compile()
        return predicate(text)

    def evaluate_record(self, record: Record) -> bool:
        try:
            predicate = self._record_predicate
        except AttributeError:
            predicate = self._record_predicate = self.compile(records=True)
        return predicate(record)


class Leaf(Node):
    """A term matched against text; on records it reads the record's whole text."""

    __slots__ = ()

    def text_predicate(self) -> TextPredicate:
        raise NotImplementedError

    def spans(self, text: str) -> Iterator[Span]:
        raise NotImplementedError

    def compile(self, records: bool = False) -> Predicate:
        predicate = self.text_predicate()
        if not records:
            return predicate
        return lambda record: predicate(record.text)

    def explain(self, subject: Subject) -> Explanation:
        text = subject.text if isinstance(subject, Record) else subject
        if not self.evaluate(text):
            return Explanation(self, False)
        spans = tuple(span for span in self.spans(text) if span[1] > span[0])
        return Explanation(self, True, spans)
