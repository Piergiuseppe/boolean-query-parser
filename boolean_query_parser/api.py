from __future__ import annotations

from typing import Iterable, List, Union

from .nodes import Node
from .services import MatchingService, ParsingService

_parsing = ParsingService()
_matching = MatchingService()


def parse_query(query_str: str, *, ignore_case: bool = False) -> Node:
    """
    Parse a boolean query into a tree that :func:`apply_query` can evaluate.

    >>> parse_query('python AND (django OR flask)')
    >>> parse_query('error NOT "permission denied"')
    >>> parse_query('/[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}/i')

    With ``ignore_case=True`` every term, regex and template matches regardless of case.
    Raises :class:`QuerySyntaxError` (a :class:`QueryError`) when the query is malformed.
    """
    return _parsing.parse(query_str, ignore_case=ignore_case)


def apply_query(
    parsed_query: Node, text_data: Union[str, Iterable[str]]
) -> Union[bool, List[str]]:
    """
    Match one text, returning a bool, or filter an iterable of texts, returning a list.

    >>> query = parse_query('python AND (django OR flask)')
    >>> apply_query(query, "This is a python flask application")
    True
    >>> apply_query(query, ["python django app", "ruby rails app"])
    ['python django app']
    """
    return _matching.apply(parsed_query, text_data)
