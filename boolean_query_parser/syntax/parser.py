from __future__ import annotations

from typing import Callable, Dict, List, Optional

from ..exceptions import QuerySyntaxError
from ..nodes import (
    AndNode,
    ComparisonNode,
    FieldNode,
    Node,
    NotNode,
    OrNode,
    RegexNode,
    TemplateNode,
    TextNode,
)
from ..options import QueryOptions
from .tokens import Token, TokenType

IMPLICIT_AND_STARTERS = frozenset({
    TokenType.TEXT,
    TokenType.WILDCARD,
    TokenType.FIELD,
    TokenType.REGEX,
    TokenType.COMPARISON,
    TokenType.TEMPLATE,
    TokenType.LPAREN,
    TokenType.NOT,
})


class Parser:
    """
    Recursive descent parser for the grammar::

        query    := or_expr
        or_expr  := and_expr ('OR' and_expr)*
        and_expr := not_expr ('AND'? not_expr)*
        not_expr := 'NOT' not_expr | FIELD not_expr | atom
        atom     := TEXT | WILDCARD | REGEX | COMPARISON | TEMPLATE | '(' or_expr ')'
    """

    def __init__(self, tokens: List[Token], options: Optional[QueryOptions] = None) -> None:
        if not tokens or tokens[-1].type is not TokenType.EOF:
            raise QuerySyntaxError("Invalid token stream, missing EOF")
        self._tokens = tokens
        self._current = 0
        self._options = options = options or QueryOptions()
        self._inside_field = False
        self._atom_builders: Dict[TokenType, Callable[[Token], Node]] = {
            TokenType.TEXT: lambda token: TextNode(
                token.value, options.ignore_case, options.whole_words
            ),
            TokenType.WILDCARD: lambda token: TextNode(
                token.value, options.ignore_case, options.whole_words, wildcard=True
            ),
            TokenType.REGEX: self._build_regex,
            TokenType.COMPARISON: lambda token: ComparisonNode(
                token.value.kind, token.value.operator, token.value.value
            ),
            TokenType.TEMPLATE: lambda token: TemplateNode(token.value, options.ignore_case),
        }

    def parse(self) -> Node:
        if self._peek().type is TokenType.EOF:
            raise QuerySyntaxError("Empty query", 0)
        node = self._parse_or(0)
        if self._peek().type is not TokenType.EOF:
            raise self._unexpected(self._peek())
        return node

    def _parse_or(self, depth: int) -> Node:
        operands = [self._parse_and(depth)]
        while self._accept(TokenType.OR):
            operands.append(self._parse_and(depth))
        return OrNode.of(operands)

    def _parse_and(self, depth: int) -> Node:
        operands = [self._parse_not(depth)]
        while True:
            if self._accept(TokenType.AND) or self._peek().type in IMPLICIT_AND_STARTERS:
                operands.append(self._parse_not(depth))
            else:
                return AndNode.of(operands)

    def _parse_not(self, depth: int) -> Node:
        token = self._peek()
        if self._accept(TokenType.NOT):
            return NotNode(self._parse_not(self._deeper(depth, token)))
        if self._accept(TokenType.FIELD):
            return self._parse_field(token, depth)
        return self._parse_atom(depth)

    def _parse_field(self, token: Token, depth: int) -> Node:
        if self._inside_field:
            raise QuerySyntaxError(
                f"Field {token.describe()} at position {token.position} is inside another field; "
                f"fields cannot be nested",
                token.position,
            )
        self._inside_field = True
        try:
            return FieldNode(token.value, self._parse_not(self._deeper(depth, token)))
        finally:
            self._inside_field = False

    def _build_regex(self, token: Token) -> Node:
        if not self._options.allow_regex:
            raise ValueError("Regular expressions are disabled for this query; quote the term to match it literally")
        return RegexNode(token.value.pattern, token.value.flags, self._options.ignore_case)

    def _parse_atom(self, depth: int) -> Node:
        token = self._advance()
        if token.type is TokenType.LPAREN:
            node = self._parse_or(self._deeper(depth, token))
            if not self._accept(TokenType.RPAREN):
                raise QuerySyntaxError(
                    f"Missing closing parenthesis for opening parenthesis at position {token.position}",
                    token.position,
                )
            return node
        build = self._atom_builders.get(token.type)
        if build is None:
            raise self._unexpected(token)
        try:
            return build(token)
        except ValueError as error:
            raise QuerySyntaxError(f"{error} (in the term at position {token.position})", token.position) from None

    def _deeper(self, depth: int, token: Token) -> int:
        if depth >= self._options.max_depth:
            raise QuerySyntaxError(
                f"Query nests deeper than {self._options.max_depth} levels at position {token.position}",
                token.position,
            )
        return depth + 1

    def _unexpected(self, token: Token) -> QuerySyntaxError:
        if token.type is TokenType.EOF:
            previous = self._tokens[self._current - 1] if self._current >= 1 else None
            after = f" after {previous.describe()}" if previous is not None else ""
            return QuerySyntaxError(f"Unexpected end of query{after}", token.position)
        return QuerySyntaxError(
            f"Unexpected token {token.describe()} at position {token.position}", token.position
        )

    def _peek(self) -> Token:
        return self._tokens[self._current]

    def _advance(self) -> Token:
        token = self._tokens[self._current]
        if token.type is not TokenType.EOF:
            self._current += 1
        return token

    def _accept(self, type: TokenType) -> bool:
        if self._peek().type is type:
            self._current += 1
            return True
        return False
