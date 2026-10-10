from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Union


class TokenType(Enum):
    AND = auto()
    OR = auto()
    NOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    TEXT = auto()
    WILDCARD = auto()
    FIELD = auto()
    REGEX = auto()
    COMPARISON = auto()
    TEMPLATE = auto()
    EOF = auto()


@dataclass(frozen=True)
class RegexLiteral:
    pattern: str
    flags: str


@dataclass(frozen=True)
class ComparisonLiteral:
    kind: str
    operator: str
    value: str


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: Union[str, RegexLiteral, ComparisonLiteral]
    position: int
    source: str = field(default="", compare=False)

    def describe(self) -> str:
        return "end of query" if self.type is TokenType.EOF else repr(self.source)
