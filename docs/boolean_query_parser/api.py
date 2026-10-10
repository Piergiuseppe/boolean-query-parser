from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, List, Union

from .explanation import Explanation
from .nodes import Node
from .options import QueryOptions
from .services import ExplanationService, MatchingService, ParsingService

_parsing = ParsingService()
_matching = MatchingService()
_explaining = ExplanationService()


def parse_query(
    query_str: str,
    *,
    ignore_case: bool = False,
    whole_words: bool = False,
    allow_regex: bool = True,
) -> Node:
    """
    Parse a boolean query into a tree that :func:`apply_query` can evaluate.

    ``ignore_case`` matches every term regardless of case. ``whole_words`` makes
    terms match only whole words. ``allow_regex=False`` rejects ``/regex/`` terms,
    which is the safe choice for queries typed by untrusted users.

    Raises :class:`QuerySyntaxError` (a :class:`QueryError`) when the query is malformed.
    """
    options = QueryOptions(ignore_case=ignore_case, whole_words=whole_words, allow_regex=allow_regex)
    return _parsing.parse(query_str, options)


def apply_query(
    parsed_query: Node, text_data: Union[str, Mapping, Iterable]
) -> Union[bool, List[Any]]:
    """
    Match one text or mapping, returning a bool, or filter an iterable of them, returning a list.

    >>> query = parse_query('python AND (django OR flask)')
    >>> apply_query(query, "This is a python flask application")
    True
    >>> apply_query(parse_query('title:python'), [{"title": "python tips"}, {"title": "rust"}])
    [{'title': 'python tips'}]
    """
    return _matching.apply(parsed_query, text_data)


def explain_query(parsed_query: Node, data: Union[str, Mapping]) -> Explanation:
    """
    Explain why a text or mapping does or does not match.

    >>> explanation = explain_query(parse_query('python NOT java'), "python rocks")
    >>> explanation.matched, explanation.hits()
    (True, [Hit(field=None, start=0, end=6)])
    >>> explanation.highlight("python rocks")
    '[python] rocks'
    """
    return _explaining.explain(parsed_query, data)
