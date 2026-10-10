from __future__ import annotations

from typing import Callable, List, Optional

from ..exceptions import QuerySyntaxError
from ..nodes.template import PLACEHOLDER
from ..values import OPERATORS
from .tokens import ComparisonLiteral, RegexLiteral, Token, TokenType

KEYWORDS = {"AND": TokenType.AND, "OR": TokenType.OR, "NOT": TokenType.NOT}
QUOTES = frozenset("\"'")
WHITESPACE = frozenset(" \t\n\r")
WORD_PUNCTUATION = frozenset("_.-+#@*")
VALUE_PUNCTUATION = frozenset("_.-+/:")


def _is_word_start(char: str) -> bool:
    return char.isalnum() or char == "_"


def _is_flag_char(char: str) -> bool:
    return char.isalnum() or char == "_"


def _is_word_char(char: str) -> bool:
    return char.isalnum() or char in WORD_PUNCTUATION


def _is_value_char(char: str) -> bool:
    return char.isalnum() or char in VALUE_PUNCTUATION


class Lexer:
    """
    Splits a query into tokens.

    Bare words may contain ``_ . - + # @`` after their first character, so
    ``node.js``, ``e-mail`` and ``C++`` need no quotes. A ``*`` anywhere in a
    bare word makes it a wildcard. ``name:`` followed by an operator is a
    comparison (``num:>5``); followed by anything else it scopes a term to a field.
    """

    def __init__(self, query: str) -> None:
        self._query = query
        self._position = 0

    def tokenize(self) -> List[Token]:
        self._position = 0
        tokens: List[Token] = []
        while True:
            self._skip_whitespace()
            if self._at_end():
                tokens.append(Token(TokenType.EOF, "", self._position))
                return tokens
            tokens.append(self._read_token())

    def _read_token(self) -> Token:
        char = self._peek()
        if char == "(":
            return self._read_symbol(TokenType.LPAREN)
        if char == ")":
            return self._read_symbol(TokenType.RPAREN)
        if char == "/":
            return self._read_regex()
        if char in QUOTES:
            return self._read_quoted()
        if _is_word_start(char) or (char == "*" and _is_word_start(self._peek(1))):
            return self._read_word()
        raise QuerySyntaxError(
            f"Unrecognized character '{char}' at position {self._position}. "
            f"Use quotes for terms containing special characters, e.g. \"{char}term\"",
            self._position,
        )

    def _read_symbol(self, type: TokenType) -> Token:
        start = self._position
        self._position += 1
        return self._token(type, self._query[start], start)

    def _read_regex(self) -> Token:
        start = self._position
        self._position += 1
        pattern = self._read_until("/", keep_escapes=True)
        if pattern is None:
            raise QuerySyntaxError(
                f"Unclosed regex at position {start}. "
                f"Regex patterns must be enclosed in forward slashes, e.g. /pattern/",
                start,
            )
        flags = self._consume_while(_is_flag_char)
        if not pattern:
            raise QuerySyntaxError(f"Empty regex at position {start}", start)
        return self._token(TokenType.REGEX, RegexLiteral(pattern, flags), start)

    def _read_quoted(self) -> Token:
        start = self._position
        text = self._read_quoted_text()
        type = TokenType.TEMPLATE if PLACEHOLDER.search(text) else TokenType.TEXT
        return self._token(type, text, start)

    def _read_quoted_text(self) -> str:
        start = self._position
        quote = self._peek()
        self._position += 1
        text = self._read_until(quote, keep_escapes=False)
        if text is None:
            raise QuerySyntaxError(f"Unclosed quote {quote} at position {start}", start)
        return text

    def _read_word(self) -> Token:
        start = self._position
        word = self._consume_while(_is_word_char)
        if self._peek() == ":":
            if self._operator_at(self._position + 1):
                return self._read_comparison(word, start)
            if "*" in word or word.upper() in KEYWORDS:
                raise QuerySyntaxError(f"Invalid field name {word!r} at position {start}", start)
            self._position += 1
            return self._token(TokenType.FIELD, word, start)
        keyword = KEYWORDS.get(word.upper())
        if keyword is not None:
            return self._token(keyword, word.upper(), start)
        if "*" in word:
            return self._token(TokenType.WILDCARD, word, start)
        return self._token(TokenType.TEXT, word, start)

    def _operator_at(self, position: int) -> bool:
        return any(self._query.startswith(symbol, position) for symbol in OPERATORS)

    def _read_comparison(self, kind: str, start: int) -> Token:
        self._position += 1
        operator = self._consume_operator()
        if self._peek() in QUOTES:
            value = self._read_quoted_text()
        else:
            value = self._consume_while(_is_value_char)
        if operator is None or not value:
            raise QuerySyntaxError(
                f"Invalid comparison {self._query[start:self._position]!r} at position {start}. "
                f"Expected e.g. num:>5 or date:<=2024-01-01",
                start,
            )
        return self._token(TokenType.COMPARISON, ComparisonLiteral(kind, operator, value), start)

    def _consume_operator(self) -> Optional[str]:
        for symbol in OPERATORS:
            if self._query.startswith(symbol, self._position):
                self._position += len(symbol)
                return symbol
        return None

    def _read_until(self, terminator: str, keep_escapes: bool) -> Optional[str]:
        query = self._query
        chars: List[str] = []
        while not self._at_end():
            char = query[self._position]
            if char == terminator:
                self._position += 1
                return "".join(chars)
            if char == "\\" and self._position + 1 < len(query):
                escaped = query[self._position + 1]
                chars.append(char + escaped if keep_escapes else escaped)
                self._position += 2
            else:
                chars.append(char)
                self._position += 1
        return None

    def _consume_while(self, accepts: Callable[[str], bool]) -> str:
        start = self._position
        query = self._query
        while self._position < len(query) and accepts(query[self._position]):
            self._position += 1
        return query[start:self._position]

    def _skip_whitespace(self) -> None:
        self._consume_while(WHITESPACE.__contains__)

    def _peek(self, offset: int = 0) -> str:
        position = self._position + offset
        return self._query[position] if position < len(self._query) else ""

    def _at_end(self) -> bool:
        return self._position >= len(self._query)

    def _token(self, type: TokenType, value, start: int) -> Token:
        return Token(type, value, start, self._query[start:self._position])
