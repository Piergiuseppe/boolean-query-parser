from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, List, Union

from ..nodes import Node
from ..records import Record

Data = Union[str, Mapping, Iterable]


class MatchingService:
    """Applies a query to a text, a mapping, or a batch of either."""

    def apply(self, query: Node, data: Data) -> Union[bool, List[Any]]:
        if isinstance(data, str):
            return query.evaluate(data)
        if isinstance(data, Mapping):
            return query.evaluate_record(Record(data))
        return self.filter(query, data)

    def filter(self, query: Node, data: Iterable) -> List[Any]:
        items = _batch(data)
        if all(isinstance(item, str) for item in items):
            return list(filter(query.compile(), items))
        if all(isinstance(item, Mapping) for item in items):
            predicate = query.compile(records=True)
            return [item for item in items if predicate(Record(item))]
        found = sorted({type(item).__name__ for item in items})
        raise TypeError(
            f"every item must be a str, or every item a mapping; got {', '.join(found)}"
        )


def _batch(data: Any) -> Union[list, tuple]:
    if isinstance(data, (bytes, bytearray)) or not isinstance(data, Iterable):
        raise TypeError(
            "text_data must be a str, a mapping, or an iterable of either, "
            f"got {type(data).__name__}"
        )
    return data if isinstance(data, (list, tuple)) else list(data)
