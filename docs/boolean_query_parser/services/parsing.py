from __future__ import annotations

from typing import Optional

from ..nodes import Node
from ..options import QueryOptions
from ..syntax import Lexer, Parser


class ParsingService:
    def parse(self, query: str, options: Optional[QueryOptions] = None) -> Node:
        if not isinstance(query, str):
            raise TypeError(f"query must be a str, got {type(query).__name__}")
        return Parser(Lexer(query).tokenize(), options).parse()
