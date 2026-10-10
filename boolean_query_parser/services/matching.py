from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import List, Union

from ..nodes import Node


class MatchingService:
    def matches(self, query: Node, text: str) -> bool:
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, got {type(text).__name__}")
        return query.evaluate(text)

    def filter(self, query: Node, texts: Iterable[str]) -> List[str]:
        if not isinstance(texts, (list, tuple)):
            texts = list(texts)
        for text in texts:
            if not isinstance(text, str):
                raise TypeError(f"every text must be a str, got {type(text).__name__}")
        return list(filter(query.compile(), texts))

    def apply(self, query: Node, data: Union[str, Iterable[str]]) -> Union[bool, List[str]]:
        if isinstance(data, str):
            return self.matches(query, data)
        if isinstance(data, Iterable) and not isinstance(data, (Mapping, bytes, bytearray)):
            return self.filter(query, data)
        raise TypeError(
            f"text_data must be a str or an iterable of str, got {type(data).__name__}"
        )
