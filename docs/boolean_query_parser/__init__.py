"""
Parse and evaluate boolean text queries: AND, OR, NOT, parentheses, regular
expressions, number and date comparisons, and positional templates.
"""

from .api import apply_query, parse_query
from .exceptions import QueryError, QuerySyntaxError
from .nodes import Node

UNINSTALLED_VERSION = "0.0.0+unknown"


def _installed_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("boolean_query_parser")
    except PackageNotFoundError:
        return UNINSTALLED_VERSION


__version__ = _installed_version()
__all__ = ["Node", "QueryError", "QuerySyntaxError", "apply_query", "parse_query"]
