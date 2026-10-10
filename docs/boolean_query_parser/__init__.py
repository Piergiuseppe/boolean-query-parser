"""
Parse and evaluate boolean text queries: AND, OR, NOT, parentheses, wildcards,
regular expressions, number, date, duration and size comparisons, positional
templates, and field-scoped terms for mappings.
"""

from .api import apply_query, explain_query, parse_query
from .exceptions import QueryError, QuerySyntaxError
from .explanation import Explanation, Hit
from .nodes import Node

UNINSTALLED_VERSION = "0.0.0+unknown"


def _installed_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("boolean_query_parser")
    except PackageNotFoundError:
        return UNINSTALLED_VERSION


__version__ = _installed_version()
__all__ = [
    "Explanation",
    "Hit",
    "Node",
    "QueryError",
    "QuerySyntaxError",
    "apply_query",
    "explain_query",
    "parse_query",
]
