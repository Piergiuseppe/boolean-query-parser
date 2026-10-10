from __future__ import annotations

import re
from typing import Iterator, List, Match, Pattern, Tuple

from ..values import KINDS, OPERATORS, ValueKind, resolve_kind
from ..values.kinds import ValueTest
from ..explanation import Span
from .base import Leaf, TextPredicate

PLACEHOLDER = re.compile(
    r"\{(" + "|".join(KINDS) + r"):("
    + "|".join(re.escape(symbol) for symbol in OPERATORS)
    + r")([^}]+)\}",
    re.IGNORECASE,
)


class TemplateNode(Leaf):
    """
    A quoted phrase with ``{kind:op value}`` placeholders, e.g. ``"took {num:<50} ms"``.

    The literal parts must appear in order, with any run of whitespace matching
    any run of whitespace, and every placeholder must pass its comparison.
    """

    __slots__ = ("template", "_regex", "_placeholders")

    def __init__(self, template: str, ignore_case: bool = False) -> None:
        self.template = template
        self._regex, self._placeholders = _build(template, ignore_case)

    def text_predicate(self) -> TextPredicate:
        search = self._regex.search
        placeholders = self._placeholders

        def predicate(text: str) -> bool:
            match = search(text)
            while match is not None:
                if _accepts(placeholders, match, text):
                    return True
                match = search(text, match.start() + 1)
            return False

        return predicate

    def spans(self, text: str) -> Iterator[Span]:
        for match in self._candidates(text):
            yield match.span()

    def _candidates(self, text: str) -> Iterator[Match[str]]:
        # Restarting one character after each candidate lets candidates
        # overlap, so a failed comparison never hides a later one.
        search = self._regex.search
        match = search(text)
        while match is not None:
            if _accepts(self._placeholders, match, text):
                yield match
            match = search(text, match.start() + 1)

    def __repr__(self) -> str:
        return f"Template({self.template!r})"


Placeholder = Tuple[int, ValueKind, ValueTest]


def _accepts(placeholders: Tuple[Placeholder, ...], match: Match[str], text: str) -> bool:
    for group, kind, test in placeholders:
        start, end = match.span(group)
        if not (test(text[start:end]) and kind.standalone(text, start, end)):
            return False
    return True


def _build(template: str, ignore_case: bool) -> Tuple[Pattern[str], Tuple[Placeholder, ...]]:
    parts: List[str] = []
    placeholders: List[Placeholder] = []
    literal_start = 0
    for placeholder in PLACEHOLDER.finditer(template):
        kind_name, operator, threshold = placeholder.groups()
        kind = resolve_kind(kind_name)
        parts.append(_literal(template[literal_start:placeholder.start()], ignore_case))
        parts.append(f"({kind.pattern})")
        placeholders.append((len(placeholders) + 1, kind, kind.bind(operator, threshold.strip())))
        literal_start = placeholder.end()
    parts.append(_literal(template[literal_start:], ignore_case))

    if not placeholders:
        raise ValueError(
            "Template must contain at least one placeholder, "
            "e.g. {num:>5} or {date:<=2024-01-01}"
        )
    return re.compile("".join(parts)), tuple(placeholders)


def _literal(text: str, ignore_case: bool) -> str:
    pattern = "".join(
        r"\s+" if chunk.isspace() else re.escape(chunk)
        for chunk in re.split(r"(\s+)", text)
        if chunk
    )
    # Scoped so that ignore_case never loosens the value patterns themselves.
    return f"(?i:{pattern})" if ignore_case and pattern else pattern
