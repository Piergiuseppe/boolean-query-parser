from __future__ import annotations

import re

from .base import Node, Predicate

FLAGS = {
    "i": re.IGNORECASE,
    "m": re.MULTILINE,
    "s": re.DOTALL,
    "x": re.VERBOSE,
}


class RegexNode(Node):
    __slots__ = ("pattern", "flags", "regex")

    def __init__(self, pattern: str, flags: str = "", ignore_case: bool = False) -> None:
        self.pattern = pattern
        self.flags = flags
        try:
            self.regex = re.compile(pattern, _flag_bits(flags, ignore_case))
        except (re.error, OverflowError, RecursionError) as error:
            raise ValueError(f"Invalid regular expression /{pattern}/: {error}") from None

    def compile(self) -> Predicate:
        search = self.regex.search
        return lambda text: search(text) is not None

    def __repr__(self) -> str:
        return f"Regex({self.pattern!r}, flags={self.flags!r})" if self.flags else f"Regex({self.pattern!r})"


def _flag_bits(flags: str, ignore_case: bool) -> int:
    unsupported = [flag for flag in dict.fromkeys(flags) if flag not in FLAGS]
    if unsupported:
        raise ValueError(
            f"Unsupported regex flag(s) {''.join(unsupported)!r}. "
            f"Supported flags: {', '.join(FLAGS)}"
        )
    bits = re.IGNORECASE if ignore_case else 0
    for flag in flags:
        bits |= FLAGS[flag]
    return bits
