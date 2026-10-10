from __future__ import annotations

import re
from typing import Iterator

from ..explanation import Span
from .base import Leaf, TextPredicate
from .wildcard import Wildcard


class TextNode(Leaf):
    """A literal term. ``*`` in a wildcard term matches any run of word characters."""

    __slots__ = ("value", "ignore_case", "whole_words", "wildcard", "_matcher")

    def __init__(
        self,
        value: str,
        ignore_case: bool = False,
        whole_words: bool = False,
        wildcard: bool = False,
    ) -> None:
        self.value = value
        self.ignore_case = ignore_case
        self.whole_words = whole_words
        self.wildcard = wildcard
        if wildcard:
            self._matcher = Wildcard(value, ignore_case, whole_words)
        else:
            pattern = re.escape(value)
            if whole_words:
                pattern = rf"(?<!\w){pattern}(?!\w)"
            self._matcher = re.compile(pattern, re.IGNORECASE if ignore_case else 0)

    def text_predicate(self) -> TextPredicate:
        if self.wildcard:
            return self._matcher.search
        if self.whole_words or self.ignore_case:
            search = self._matcher.search
            return lambda text: search(text) is not None
        value = self.value
        return lambda text: value in text

    def spans(self, text: str) -> Iterator[Span]:
        if self.wildcard:
            yield from self._matcher.spans(text)
            return
        for match in self._matcher.finditer(text):
            yield match.span()

    def __repr__(self) -> str:
        return f"Text({self.value!r})"
