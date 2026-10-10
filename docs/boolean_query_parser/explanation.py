from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, List, Optional, Tuple

Span = Tuple[int, int]


@dataclass(frozen=True)
class Hit:
    """Where a term matched: ``field`` is None for the text itself or for a record's unscoped text."""

    field: Optional[str]
    start: int
    end: int


@dataclass(frozen=True)
class Explanation:
    """Why a query did or did not match, as a tree mirroring the query."""

    node: Any
    matched: bool
    spans: Tuple[Span, ...] = ()
    children: Tuple[Explanation, ...] = ()
    field: Optional[str] = None
    negates: bool = False

    def hits(self) -> List[Hit]:
        """The places that made the query match. Terms under NOT never count."""
        return list(self._hits(None))

    def _hits(self, field: Optional[str]) -> Iterator[Hit]:
        if self.negates or not self.matched:
            return
        field = self.field if self.field is not None else field
        for start, end in self.spans:
            yield Hit(field, start, end)
        for child in self.children:
            yield from child._hits(field)

    def highlight(self, text: str, before: str = "[", after: str = "]") -> str:
        spans = _merge((hit.start, hit.end) for hit in self.hits() if hit.field is None)
        parts: List[str] = []
        cursor = 0
        for start, end in spans:
            parts += [text[cursor:start], before, text[start:end], after]
            cursor = end
        parts.append(text[cursor:])
        return "".join(parts)

    def render(self) -> str:
        return "\n".join(self._lines(0))

    def _lines(self, depth: int) -> Iterator[str]:
        mark = "✓" if self.matched else "✗"
        where = ", ".join(f"{start}-{end}" for start, end in self.spans)
        suffix = f"  at {where}" if where else ""
        yield f"{'  ' * depth}{mark} {self.node.label()}{suffix}"
        for child in self.children:
            yield from child._lines(depth + 1)

    def __str__(self) -> str:
        return self.render()


def _merge(spans) -> List[Span]:
    merged: List[Span] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged
