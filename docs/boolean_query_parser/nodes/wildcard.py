from __future__ import annotations

import re
from bisect import bisect_left
from typing import Dict, Iterator, List, Tuple

Span = Tuple[int, int]

_WORD_RUN = re.compile(r"\w+")
_WORD_CHAR = re.compile(r"\w")


class Wildcard:
    """A term where ``*`` stands for any run of word characters.

    Matching tracks the set of positions every prefix of the term can reach,
    one segment at a time, so it stays linear in the text for each segment.
    A regex with ``\\w*`` per star would backtrack exponentially on terms like
    ``a*a*a*b``, which matters when queries come from untrusted users.
    """

    __slots__ = ("_segments", "_whole_words")

    def __init__(self, term: str, ignore_case: bool, whole_words: bool) -> None:
        flags = re.IGNORECASE if ignore_case else 0
        self._segments = [re.compile(f"(?=({re.escape(part)}))", flags) for part in term.split("*")]
        self._whole_words = whole_words

    def search(self, text: str) -> bool:
        for _ in self.spans(text):
            return True
        return False

    def spans(self, text: str) -> Iterator[Span]:
        run_end = _run_ends(text)
        reached = self._starts(text)
        for segment in self._segments[1:]:
            if not reached:
                return
            reached = _extend(reached, segment, text, run_end)
        for end, start in reached.items():
            if not self._whole_words or not _is_word(text, end):
                yield start, end

    def _starts(self, text: str) -> Dict[int, int]:
        reached: Dict[int, int] = {}
        for match in self._segments[0].finditer(text):
            start, end = match.span(1)
            if self._whole_words and _is_word(text, start - 1):
                continue
            reached.setdefault(end, start)
        return reached


def _extend(reached: Dict[int, int], segment, text: str, run_end: List[int]) -> Dict[int, int]:
    # A star can cover text[e:j] only when it is all word characters, i.e.
    # e <= j <= run_end[e]. Reached positions sharing a run_end form one interval.
    intervals: Dict[int, Tuple[int, int]] = {}
    for end, start in reached.items():
        limit = run_end[end]
        if limit not in intervals or end < intervals[limit][0]:
            intervals[limit] = (end, start)
    limits = sorted(intervals)
    extended: Dict[int, int] = {}
    for match in segment.finditer(text):
        position, end = match.span(1)
        index = bisect_left(limits, position)
        if index == len(limits):
            break
        lowest, start = intervals[limits[index]]
        if lowest <= position:
            extended.setdefault(end, start)
    return extended


def _run_ends(text: str) -> List[int]:
    ends = list(range(len(text) + 1))
    for run in _WORD_RUN.finditer(text):
        run_start, run_stop = run.span()
        ends[run_start:run_stop] = [run_stop] * (run_stop - run_start)
    return ends


def _is_word(text: str, index: int) -> bool:
    return 0 <= index < len(text) and _WORD_CHAR.match(text, index) is not None
