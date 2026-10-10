from __future__ import annotations

from typing import Callable, Dict, List

from ..exceptions import QuerySyntaxError
from ..nodes import (
    AndNode,
    ComparisonNode,
    Node,
    NotNode,
    OrNode,
    RegexNode,
    TemplateNode,
    TextNode,
)
from .tokens import Token, TokenType

MAX_DEPTH = 100

IMPLICIT_AND_STARTERS = frozenset({
    TokenType.TEXT,
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
        not_expr := 'NOT' not_expr | atom
        atom     := TEXT | REGEX | COMPARISON | TEMPLATE | '(' or_expr ')'
    """

    def __init__(
        self,
        tokens: List[Token],
        ignore_case: bool = False,
        max_depth: int = MAX_DEPTH,
    ) -> None:
        if not tokens or tokens[-1].type is not TokenType.EOF:
            raise QuerySyntaxError("Invalid token stream, missing EOF")
        self._tokens = tokens
        self._current = 0
        self._ignore_case = ignore_case
        self._max_depth = max_depth
        self._atom_builders: Dict[TokenType, Callable[[Token], Node]] = {
            TokenType.TEXT: lambda token: TextNode(token.value, ignore_case),
            TokenType.REGEX: lambda token: RegexNode(token.value.pattern, token.value.flags, ignore_case),
            TokenType.COMPARISON: lambda token: ComparisonNode(
                token.value.kind, token.value.operator, token.value.value
            ),
            TokenType.TEMPLATE: lambda token: TemplateNode(token.value, ignore_case),
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
        return self._parse_atom(depth)

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
        if depth >= self._max_depth:
            raise QuerySyntaxError(
                f"Query nests deeper than {self._max_depth} levels at position {token.position}",
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
