"""
Boolean Query Parser

This module provides functionality for parsing and evaluating boolean text queries.
It supports AND, OR, NOT operations, parentheses for nested expressions,
and regular expressions for text matching.
"""

import re
from enum import Enum, auto
from typing import Callable, List, Union


class TokenType(Enum):
    """Enum representing types of tokens in a boolean query."""
    AND = auto()
    OR = auto()
    NOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    TEXT = auto()
    REGEX = auto()
    EOF = auto()


class Token:
    """Represents a token in the boolean query language."""
    __slots__ = ('type', 'value', 'position')

    def __init__(self, type: TokenType, value: str, position: int):
        self.type = type
        self.value = value
        self.position = position

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, {self.position})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Token):
            return NotImplemented
        return self.type == other.type and self.value == other.value and self.position == other.position


class Lexer:
    """
    Tokenizes a boolean query string into a sequence of tokens.

    Supports operators: AND, OR, NOT, (, ), and text/regex literals.
    """
    __slots__ = ('query', 'position', 'tokens')

    def __init__(self, query: str):
        """Initialize the lexer with a query string."""
        self.query = query
        self.position = 0
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        """
        Convert the query string into a list of tokens.

        Returns:
            List[Token]: The tokenized query
        """
        # Cache instance attributes as locals for faster access in the loop
        query = self.query
        query_len = len(query)
        tokens = self.tokens
        position = self.position

        while position < query_len:
            current_char = query[position]

            # Skip whitespace — explicit char checks are faster than .isspace()
            if current_char == ' ' or current_char == '\t' or current_char == '\n' or current_char == '\r':
                position += 1
                continue

            # Handle operators and parentheses
            if current_char == '(':
                tokens.append(Token(TokenType.LPAREN, '(', position))
                position += 1
            elif current_char == ')':
                tokens.append(Token(TokenType.RPAREN, ')', position))
                position += 1
            # Handle regex patterns (enclosed in forward slashes)
            elif current_char == '/':
                self.position = position
                regex_pattern = self._extract_regex()
                position = self.position
                if regex_pattern:
                    tokens.append(Token(TokenType.REGEX, regex_pattern, position - len(regex_pattern) - 2))
            # Handle text or keywords
            elif current_char.isalnum() or current_char in ('_', '"', "'"):
                self.position = position
                text = self._extract_text()
                position = self.position
                upper_text = text.upper()

                if upper_text == 'AND':
                    tokens.append(Token(TokenType.AND, 'AND', position - 3))
                elif upper_text == 'OR':
                    tokens.append(Token(TokenType.OR, 'OR', position - 2))
                elif upper_text == 'NOT':
                    tokens.append(Token(TokenType.NOT, 'NOT', position - 3))
                else:
                    tokens.append(Token(TokenType.TEXT, text, position - len(text)))
            else:
                raise ValueError(
                    f"Unrecognized character '{current_char}' at position {position}. "
                    f"Use quotes for terms containing special characters, e.g. \"{current_char}term\""
                )

        # Add EOF token
        tokens.append(Token(TokenType.EOF, '', position))
        self.position = position
        return tokens

    def _extract_regex(self) -> str:
        """
        Extract a regex pattern enclosed in forward slashes, including any flags.

        Returns:
            str: The extracted regex pattern and flags
        """
        query = self.query
        query_len = len(query)
        start_pos = self.position
        pos = start_pos + 1  # Skip opening slash

        # If we're at the end of the string already, return empty
        if pos >= query_len:
            return ""

        # Find closing slash — build content with list for O(n) concatenation
        parts: list = []
        parts_append = parts.append
        while pos < query_len and query[pos] != '/':
            # Handle escaped characters
            if query[pos] == '\\' and pos + 1 < query_len:
                parts_append(query[pos:pos + 2])
                pos += 2
            else:
                parts_append(query[pos])
                pos += 1

        # Skip closing slash if found
        if pos < query_len and query[pos] == '/':
            pos += 1

            # Extract any regex flags (i, g, m, etc.)
            flags_parts: list = []
            while pos < query_len and query[pos].isalpha():
                flags_parts.append(query[pos])
                pos += 1

            self.position = pos
            content = ''.join(parts)

            if flags_parts:
                return f"{content}/{''.join(flags_parts)}"
            return content
        else:
            # Unclosed regex, revert position
            self.position = start_pos
            return ""

    def _extract_text(self) -> str:
        """
        Extract a text token, which could be a quoted string or a regular word.

        Returns:
            str: The extracted text
        """
        query = self.query
        query_len = len(query)
        pos = self.position

        # Check if it's a quoted string — tuple is faster than list for 'in'
        if query[pos] in ('"', "'"):
            quote_char = query[pos]
            pos += 1  # Skip opening quote

            parts: list = []
            parts_append = parts.append
            while pos < query_len and query[pos] != quote_char:
                # Handle escaped characters in quotes
                if query[pos] == '\\' and pos + 1 < query_len:
                    parts_append(query[pos + 1])
                    pos += 2
                else:
                    parts_append(query[pos])
                    pos += 1

            # Skip closing quote if found
            if pos < query_len:
                pos += 1

            self.position = pos
            return ''.join(parts)

        # Regular word — slice at the end instead of char-by-char concatenation
        start = pos
        while pos < query_len:
            c = query[pos]
            if c.isalnum() or c == '_':
                pos += 1
            else:
                break

        self.position = pos
        return query[start:pos]


class Node:
    """Base class for AST nodes in the boolean query parser."""
    __slots__ = ()

    def evaluate(self, text: str) -> bool:
        """
        Evaluate this node against the provided text.

        Args:
            text: The text to evaluate against

        Returns:
            bool: True if the node's condition matches the text, False otherwise
        """
        raise NotImplementedError("Subclasses must implement evaluate()")

    def _compile(self) -> Callable[[str], bool]:
        """
        Compile this node into a fast closure for repeated evaluation.

        Returns a plain function that avoids method dispatch and attribute
        lookups, giving a significant speedup when evaluating many texts.
        """
        raise NotImplementedError("Subclasses must implement _compile()")


class TextNode(Node):
    """Node representing a text literal in the query."""
    __slots__ = ('value',)

    def __init__(self, value: str):
        self.value = value

    def evaluate(self, text: str) -> bool:
        """Return True if the node's text value is found in the input text."""
        return self.value in text

    def _compile(self) -> Callable[[str], bool]:
        value = self.value  # capture as closure local (LOAD_DEREF vs LOAD_ATTR)
        def _eval(text: str) -> bool:
            return value in text
        return _eval

    def __repr__(self) -> str:
        return f"Text({self.value!r})"


class RegexNode(Node):
    """Node representing a regular expression pattern in the query."""
    __slots__ = ('pattern', 'regex')

    VALID_FLAGS = frozenset('imsx')

    def __init__(self, pattern: str):
        self.pattern = pattern

        # Handle regex flags.
        # The Lexer stores the token value as "pattern/flags" when flags are present,
        # or just "pattern" when there are none. We use rfind to only split on the
        # *last* '/' so that forward slashes inside the pattern (e.g. escaped \/) are
        # preserved correctly.
        flags = 0
        last_slash = pattern.rfind('/')
        if last_slash > 0:
            possible_flags = pattern[last_slash + 1:]
            if possible_flags and all(c in self.VALID_FLAGS for c in possible_flags):
                flag_str = possible_flags
                pattern = pattern[:last_slash]

                if 'i' in flag_str:
                    flags |= re.IGNORECASE
                if 'm' in flag_str:
                    flags |= re.MULTILINE
                if 's' in flag_str:
                    flags |= re.DOTALL
                if 'x' in flag_str:
                    flags |= re.VERBOSE

        try:
            self.regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regular expression: {pattern}. Error: {e}")

    def evaluate(self, text: str) -> bool:
        """Return True if the regex pattern matches the input text."""
        return self.regex.search(text) is not None

    def _compile(self) -> Callable[[str], bool]:
        search = self.regex.search  # bind method once (avoids attr lookup per call)
        def _eval(text: str) -> bool:
            return search(text) is not None
        return _eval

    def __repr__(self) -> str:
        return f"Regex({self.pattern!r})"


class NotNode(Node):
    """Node representing a NOT operation in the query."""
    __slots__ = ('child',)

    def __init__(self, child: Node):
        self.child = child

    def evaluate(self, text: str) -> bool:
        """Return the negation of the child node's evaluation."""
        return not self.child.evaluate(text)

    def _compile(self) -> Callable[[str], bool]:
        child_eval = self.child._compile()
        def _eval(text: str) -> bool:
            return not child_eval(text)
        return _eval

    def __repr__(self) -> str:
        return f"NOT({self.child!r})"


class AndNode(Node):
    """Node representing an AND operation in the query."""
    __slots__ = ('left', 'right')

    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def evaluate(self, text: str) -> bool:
        """Return True if both child nodes evaluate to True."""
        return self.left.evaluate(text) and self.right.evaluate(text)

    def _compile(self) -> Callable[[str], bool]:
        left_eval = self.left._compile()
        right_eval = self.right._compile()
        def _eval(text: str) -> bool:
            return left_eval(text) and right_eval(text)
        return _eval

    def __repr__(self) -> str:
        return f"({self.left!r} AND {self.right!r})"


class OrNode(Node):
    """Node representing an OR operation in the query."""
    __slots__ = ('left', 'right')

    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def evaluate(self, text: str) -> bool:
        """Return True if either child node evaluates to True."""
        return self.left.evaluate(text) or self.right.evaluate(text)

    def _compile(self) -> Callable[[str], bool]:
        left_eval = self.left._compile()
        right_eval = self.right._compile()
        def _eval(text: str) -> bool:
            return left_eval(text) or right_eval(text)
        return _eval

    def __repr__(self) -> str:
        return f"({self.left!r} OR {self.right!r})"


class Parser:
    """
    Parses a tokenized boolean query into an abstract syntax tree (AST).

    Implements a recursive descent parser with the following grammar:
    query    := or_expr
    or_expr  := and_expr ('OR' and_expr)*
    and_expr := not_expr ('AND'? not_expr)*   (implicit AND supported)
    not_expr := 'NOT' not_expr | atom
    atom     := TEXT | REGEX | '(' query ')'
    """
    __slots__ = ('tokens', 'current', '_num_tokens')

    # Token types that can start an implicit AND operand
    _IMPLICIT_AND_STARTERS = frozenset({
        TokenType.TEXT, TokenType.REGEX, TokenType.LPAREN, TokenType.NOT
    })

    def __init__(self, tokens: List[Token]):
        """Initialize the parser with a list of tokens."""
        self.tokens = tokens
        self.current = 0
        self._num_tokens = len(tokens)

    def parse(self) -> Node:
        """
        Parse the tokens into an AST.

        Returns:
            Node: The root node of the AST

        Raises:
            ValueError: If the query has syntax errors
        """
        tokens = self.tokens
        if not tokens or tokens[-1].type != TokenType.EOF:
            raise ValueError("Invalid token stream, missing EOF")

        if self._num_tokens == 1:  # Only EOF
            raise ValueError("Empty query")

        result = self._parse_or_expr()

        # Check that we've consumed all tokens except EOF
        if self.current < self._num_tokens - 1:
            unexpected_token = tokens[self.current]
            raise ValueError(f"Unexpected token at position {unexpected_token.position}: {unexpected_token.value}")

        return result

    def _parse_or_expr(self) -> Node:
        """Parse an OR expression (a series of AND expressions joined by OR)."""
        left = self._parse_and_expr()
        tokens = self.tokens

        while self.current < self._num_tokens and tokens[self.current].type == TokenType.OR:
            self.current += 1  # Consume OR
            right = self._parse_and_expr()
            left = OrNode(left, right)

        return left

    def _parse_and_expr(self) -> Node:
        """
        Parse an AND expression (a series of NOT expressions joined by AND).

        Supports both explicit AND and implicit AND (adjacent terms without an
        operator are treated as AND, e.g. ``python java`` is ``python AND java``).
        """
        left = self._parse_not_expr()
        tokens = self.tokens
        num_tokens = self._num_tokens
        implicit_starters = self._IMPLICIT_AND_STARTERS

        while self.current < num_tokens:
            ttype = tokens[self.current].type

            if ttype == TokenType.AND:
                self.current += 1  # Consume explicit AND
                right = self._parse_not_expr()
                left = AndNode(left, right)
            elif ttype in implicit_starters:
                # Implicit AND: next token starts a new expression without an operator
                right = self._parse_not_expr()
                left = AndNode(left, right)
            else:
                break

        return left

    def _parse_not_expr(self) -> Node:
        """Parse a NOT expression."""
        if self.current < self._num_tokens and self.tokens[self.current].type == TokenType.NOT:
            self.current += 1  # Consume NOT
            expr = self._parse_not_expr()  # NOT is right-associative
            return NotNode(expr)

        return self._parse_atom()

    def _parse_atom(self) -> Node:
        """Parse an atomic expression (text, regex, or parenthesized expression)."""
        if self.current >= self._num_tokens:
            raise ValueError("Unexpected end of query")

        token = self.tokens[self.current]
        ttype = token.type

        if ttype == TokenType.TEXT:
            self.current += 1  # Consume TEXT
            return TextNode(token.value)

        elif ttype == TokenType.REGEX:
            self.current += 1  # Consume REGEX
            return RegexNode(token.value)

        elif ttype == TokenType.LPAREN:
            self.current += 1  # Consume '('
            expr = self._parse_or_expr()

            if self.current >= self._num_tokens or self.tokens[self.current].type != TokenType.RPAREN:
                raise ValueError(f"Missing closing parenthesis for opening parenthesis at position {token.position}")

            self.current += 1  # Consume ')'
            return expr

        else:
            raise ValueError(f"Unexpected token at position {token.position}: {token.value}")


class QueryError(Exception):
    """Exception raised for errors during query parsing or evaluation."""
    pass


def parse_query(query_str: str) -> Node:
    """
    Parse a boolean query string into an AST.

    This function handles the lexing and parsing stages, converting a string like
    "search AND (terms OR /regex/) NOT excluded" into an executable AST.

    Args:
        query_str: The boolean query string to parse

    Returns:
        Node: The root node of the parsed AST

    Raises:
        QueryError: If the query has syntax errors

    Examples:
        >>> ast = parse_query('python AND (django OR flask)')
        >>> ast = parse_query('error NOT "permission denied"')  # implicit AND
        >>> ast = parse_query('/[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}/i')  # email regex
    """
    try:
        lexer = Lexer(query_str)
        tokens = lexer.tokenize()

        parser = Parser(tokens)
        return parser.parse()

    except ValueError as e:
        raise QueryError(f"Error parsing query: {e}")


def apply_query(parsed_query: Node, text_data: Union[str, List[str]]) -> Union[bool, List[str]]:
    """
    Apply a parsed boolean query to text data.

    Args:
        parsed_query: The parsed query AST (from parse_query)
        text_data: Either a single string to evaluate or a list of strings to filter

    Returns:
        If text_data is a string: bool indicating if the query matches
        If text_data is a list: List of strings that match the query

    Examples:
        >>> query = parse_query('python AND (django OR flask)')
        >>> apply_query(query, "This is a python flask application")
        True
        >>> apply_query(query, ["python django app", "ruby rails app", "python numpy code"])
        ["python django app"]
    """
    if isinstance(text_data, str):
        try:
            return parsed_query.evaluate(text_data)
        except Exception as e:
            raise QueryError(f"Error evaluating query: {e}")

    elif isinstance(text_data, list):
        try:
            # Compile the AST into a closure and use C-level filter() for
            # maximum throughput when filtering large document collections.
            return list(filter(parsed_query._compile(), text_data))
        except Exception as e:
            raise QueryError(f"Error evaluating query: {e}")

    else:
        raise TypeError(
            f"text_data must be a str or list of str, got {type(text_data).__name__}"
        )
