"""The 1.0 import path. The public names still live here; token and node internals changed in 1.1."""

from .api import apply_query, parse_query
from .exceptions import QueryError, QuerySyntaxError
from .nodes import (
    AndNode,
    ComparisonNode,
    Node,
    NotNode,
    OrNode,
    RegexNode,
    TemplateNode,
    TextNode,
)
from .syntax import Lexer, Parser, Token, TokenType

__all__ = [
    "AndNode",
    "ComparisonNode",
    "Lexer",
    "Node",
    "NotNode",
    "OrNode",
    "Parser",
    "QueryError",
    "QuerySyntaxError",
    "RegexNode",
    "TemplateNode",
    "TextNode",
    "Token",
    "TokenType",
    "apply_query",
    "parse_query",
]
