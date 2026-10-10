from __future__ import annotations

from ..nodes import Node
from ..syntax import MAX_DEPTH, Lexer, Parser


class ParsingService:
    def __init__(self, max_depth: int = MAX_DEPTH) -> None:
        self._max_depth = max_depth

    def parse(self, query: str, ignore_case: bool = False) -> Node:
        if not isinstance(query, str):
            raise TypeError(f"query must be a str, got {type(query).__name__}")
        tokens = Lexer(query).tokenize()
        return Parser(tokens, ignore_case=ignore_case, max_depth=self._max_depth).parse()
