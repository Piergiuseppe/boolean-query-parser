"""
Boolean Query Parser

A package for parsing and evaluating boolean text queries with support for
AND, OR, NOT operations, parentheses for nested expressions, and regular expressions.
"""

from boolean_query_parser.parser import QueryError, apply_query, parse_query

__all__ = ['parse_query', 'apply_query', 'QueryError']

