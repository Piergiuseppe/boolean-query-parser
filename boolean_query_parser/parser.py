"""
Boolean Query Parser

This module provides functionality for parsing and evaluating boolean text queries.
It supports AND, OR, NOT operations, parentheses for nested expressions,
and regular expressions for text matching.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Union


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


@dataclass
class Token:
    """Represents a token in the boolean query language."""
    type: TokenType
    value: str
    position: int


class Lexer:
    """
    Tokenizes a boolean query string into a sequence of tokens.
    
    Supports operators: AND, OR, NOT, (, ), and text/regex literals.
    """
    
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
        while self.position < len(self.query):
            current_char = self.query[self.position]
            
            # Skip whitespace
            if current_char.isspace():
                self.position += 1
                continue
            
            # Handle operators and parentheses
            if current_char == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', self.position))
                self.position += 1
            elif current_char == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', self.position))
                self.position += 1
            # Handle regex patterns (enclosed in forward slashes)
            elif current_char == '/':
                regex_pattern = self._extract_regex()
                if regex_pattern:
                    self.tokens.append(Token(TokenType.REGEX, regex_pattern, self.position - len(regex_pattern) - 2))
            # Handle text or keywords
            elif current_char.isalnum() or current_char == '_' or current_char == '"' or current_char == "'":
                text = self._extract_text()
                upper_text = text.upper()
                
                if upper_text == 'AND':
                    self.tokens.append(Token(TokenType.AND, 'AND', self.position - 3))
                elif upper_text == 'OR':
                    self.tokens.append(Token(TokenType.OR, 'OR', self.position - 2))
                elif upper_text == 'NOT':
                    self.tokens.append(Token(TokenType.NOT, 'NOT', self.position - 3))
                else:
                    self.tokens.append(Token(TokenType.TEXT, text, self.position - len(text)))
            else:
                # Skip unrecognized characters
                self.position += 1
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.position))
        return self.tokens
    
    def _extract_regex(self) -> str:
        """
        Extract a regex pattern enclosed in forward slashes, including any flags.
        
        Returns:
            str: The extracted regex pattern and flags
        """
        start_pos = self.position
        self.position += 1  # Skip opening slash
        
        # If we're at the end of the string already, return empty
        if self.position >= len(self.query):
            return ""
        
        # Find closing slash
        content = ""
        while self.position < len(self.query) and self.query[self.position] != '/':
            # Handle escaped characters
            if self.query[self.position] == '\\' and self.position + 1 < len(self.query):
                content += self.query[self.position:self.position+2]
                self.position += 2
            else:
                content += self.query[self.position]
                self.position += 1
        
        # Skip closing slash if found
        if self.position < len(self.query) and self.query[self.position] == '/':
            self.position += 1
            
            # Extract any regex flags (i, g, m, etc.)
            flags = ""
            while self.position < len(self.query) and self.query[self.position].isalpha():
                flags += self.query[self.position]
                self.position += 1
            
            if flags:
                return f"{content}/{flags}"
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
        start_pos = self.position
        
        # Check if it's a quoted string
        if self.query[start_pos] in ['"', "'"]:
            quote_char = self.query[start_pos]
            self.position += 1  # Skip opening quote
            
            content = ""
            while self.position < len(self.query) and self.query[self.position] != quote_char:
                # Handle escaped characters in quotes
                if self.query[self.position] == '\\' and self.position + 1 < len(self.query):
                    content += self.query[self.position+1]
                    self.position += 2
                else:
                    content += self.query[self.position]
                    self.position += 1
            
            # Skip closing quote if found
            if self.position < len(self.query):
                self.position += 1
            
            return content
        
        # Regular word
        word = ""
        while (self.position < len(self.query) and 
               (self.query[self.position].isalnum() or self.query[self.position] == '_')):
            word += self.query[self.position]
            self.position += 1
        
        return word


class Node:
    """Base class for AST nodes in the boolean query parser."""
    def evaluate(self, text: str) -> bool:
        """
        Evaluate this node against the provided text.
        
        Args:
            text: The text to evaluate against
            
        Returns:
            bool: True if the node's condition matches the text, False otherwise
        """
        raise NotImplementedError("Subclasses must implement evaluate()")


class TextNode(Node):
    """Node representing a text literal in the query."""
    def __init__(self, value: str):
        self.value = value
    
    def evaluate(self, text: str) -> bool:
        """Return True if the node's text value is found in the input text."""
        return self.value in text
    
    def __repr__(self) -> str:
        return f"Text({self.value!r})"


class RegexNode(Node):
    """Node representing a regular expression pattern in the query."""
    def __init__(self, pattern: str):
        self.pattern = pattern
        
        # Handle regex flags
        flags = 0
        if '/' in pattern and not pattern.endswith('\\/'): 
            parts = pattern.split('/')
            if len(parts) > 1 and parts[-1]:  # If there are flags after the last slash
                flag_str = parts[-1]
                pattern = '/'.join(parts[:-1])  # Remove flags from pattern
                
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
        return bool(self.regex.search(text))
    
    def __repr__(self) -> str:
        return f"Regex({self.pattern!r})"


class NotNode(Node):
    """Node representing a NOT operation in the query."""
    def __init__(self, child: Node):
        self.child = child
    
    def evaluate(self, text: str) -> bool:
        """Return the negation of the child node's evaluation."""
        return not self.child.evaluate(text)
    
    def __repr__(self) -> str:
        return f"NOT({self.child!r})"


class AndNode(Node):
    """Node representing an AND operation in the query."""
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right
    
    def evaluate(self, text: str) -> bool:
        """Return True if both child nodes evaluate to True."""
        # Short-circuit evaluation
        return self.left.evaluate(text) and self.right.evaluate(text)
    
    def __repr__(self) -> str:
        return f"({self.left!r} AND {self.right!r})"


class OrNode(Node):
    """Node representing an OR operation in the query."""
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right
    
    def evaluate(self, text: str) -> bool:
        """Return True if either child node evaluates to True."""
        # Short-circuit evaluation
        return self.left.evaluate(text) or self.right.evaluate(text)
    
    def __repr__(self) -> str:
        return f"({self.left!r} OR {self.right!r})"


class Parser:
    """
    Parses a tokenized boolean query into an abstract syntax tree (AST).
    
    Implements a recursive descent parser with the following grammar:
    query   := or_expr
    or_expr := and_expr ('OR' and_expr)*
    and_expr := not_expr ('AND' not_expr)*
    not_expr := 'NOT' not_expr | atom
    atom    := TEXT | REGEX | '(' query ')'
    """
    
    def __init__(self, tokens: List[Token]):
        """Initialize the parser with a list of tokens."""
        self.tokens = tokens
        self.current = 0
    
    def parse(self) -> Node:
        """
        Parse the tokens into an AST.
        
        Returns:
            Node: The root node of the AST
        
        Raises:
            ValueError: If the query has syntax errors
        """
        if not self.tokens or self.tokens[-1].type != TokenType.EOF:
            raise ValueError("Invalid token stream, missing EOF")
        
        if len(self.tokens) == 1:  # Only EOF
            raise ValueError("Empty query")
        
        result = self._parse_or_expr()
        
        # Check that we've consumed all tokens except EOF
        if self.current < len(self.tokens) - 1:
            unexpected_token = self.tokens[self.current]
            raise ValueError(f"Unexpected token at position {unexpected_token.position}: {unexpected_token.value}")
        
        return result
    
    def _parse_or_expr(self) -> Node:
        """Parse an OR expression (a series of AND expressions joined by OR)."""
        left = self._parse_and_expr()
        
        while self.current < len(self.tokens) and self.tokens[self.current].type == TokenType.OR:
            self.current += 1  # Consume OR
            right = self._parse_and_expr()
            left = OrNode(left, right)
        
        return left
    
    def _parse_and_expr(self) -> Node:
        """Parse an AND expression (a series of NOT expressions joined by AND)."""
        left = self._parse_not_expr()
        
        while self.current < len(self.tokens) and self.tokens[self.current].type == TokenType.AND:
            self.current += 1  # Consume AND
            right = self._parse_not_expr()
            left = AndNode(left, right)
        
        return left
    
    def _parse_not_expr(self) -> Node:
        """Parse a NOT expression."""
        if self.current < len(self.tokens) and self.tokens[self.current].type == TokenType.NOT:
            self.current += 1  # Consume NOT
            expr = self._parse_not_expr()  # NOT is right-associative
            return NotNode(expr)
        
        return self._parse_atom()
    
    def _parse_atom(self) -> Node:
        """Parse an atomic expression (text, regex, or parenthesized expression)."""
        if self.current >= len(self.tokens):
            raise ValueError("Unexpected end of query")
        
        token = self.tokens[self.current]
        
        if token.type == TokenType.TEXT:
            self.current += 1  # Consume TEXT
            return TextNode(token.value)
        
        elif token.type == TokenType.REGEX:
            self.current += 1  # Consume REGEX
            return RegexNode(token.value)
        
        elif token.type == TokenType.LPAREN:
            self.current += 1  # Consume '('
            expr = self._parse_or_expr()
            
            if self.current >= len(self.tokens) or self.tokens[self.current].type != TokenType.RPAREN:
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
        >>> ast = parse_query('error NOT "permission denied"')
        >>> ast = parse_query('/[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}/') # email regex
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
            return [text for text in text_data if parsed_query.evaluate(text)]
        except Exception as e:
            raise QueryError(f"Error evaluating query: {e}")
