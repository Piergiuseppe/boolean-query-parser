from __future__ import annotations

import operator
from typing import Any, Callable, Dict

Operator = Callable[[Any, Any], bool]

# Two-character symbols come first: the lexer takes the first one that matches.
OPERATORS: Dict[str, Operator] = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "=": operator.eq,
}


def resolve_operator(symbol: str) -> Operator:
    try:
        return OPERATORS[symbol]
    except KeyError:
        raise ValueError(
            f"Unknown comparison operator {symbol!r}. "
            f"Supported operators: {', '.join(OPERATORS)}"
        ) from None
