from __future__ import annotations

from dataclasses import dataclass

MAX_DEPTH = 100


@dataclass(frozen=True)
class QueryOptions:
    ignore_case: bool = False
    whole_words: bool = False
    allow_regex: bool = True
    max_depth: int = MAX_DEPTH
