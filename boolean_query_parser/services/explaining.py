from __future__ import annotations

from collections.abc import Mapping
from typing import Union

from ..explanation import Explanation
from ..nodes import Node
from ..records import Record


class ExplanationService:
    def explain(self, query: Node, data: Union[str, Mapping]) -> Explanation:
        if isinstance(data, str):
            return query.explain(data)
        if isinstance(data, Mapping):
            return query.explain(Record(data))
        raise TypeError(f"can only explain a str or a mapping, got {type(data).__name__}")
