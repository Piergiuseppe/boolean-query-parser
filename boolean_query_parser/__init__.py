"""
Boolean Query Parser

A package for parsing and evaluating boolean text queries with support for
AND, OR, NOT operations, parentheses for nested expressions, and regular expressions.
"""

from boolean_query_parser.parser import QueryError, apply_query, parse_query

__version__ = "1.0.2"
__all__ = ['parse_query', 'apply_query', 'QueryError']

