from __future__ import annotations

from typing import Optional


class QueryError(Exception):
    pass


class QuerySyntaxError(QueryError, ValueError):
    def __init__(self, message: str, position: Optional[int] = None) -> None:
        self.message = message
        self.position = position
        super().__init__(f"Error parsing query: {message}")
