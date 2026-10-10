from __future__ import annotations

from typing import IO, Optional

from .search import Line

RESET = "\033[0m"
MATCH = "\033[1;31m"
FILENAME = "\033[35m"
NUMBER = "\033[32m"
SEPARATOR = "\033[36m"


class Printer:
    def __init__(
        self, out: IO[str], *, color: bool, highlight: bool, line_numbers: bool, filenames: bool, explain: bool
    ) -> None:
        self._out = out
        self._color = color
        self._highlight = highlight
        self._explain = explain
        self._line_numbers = line_numbers
        self._filenames = filenames

    def line(self, name: str, line: Line) -> None:
        prefix = ""
        if self._filenames:
            prefix += self._paint(name, FILENAME) + self._paint(":", SEPARATOR)
        if self._line_numbers:
            prefix += self._paint(str(line.number), NUMBER) + self._paint(":", SEPARATOR)
        self._out.write(prefix + self._body(line) + "\n")
        if self._explain and line.explanation is not None:
            for row in line.explanation.render().splitlines():
                self._out.write(f"    {row}\n")

    def count(self, name: str, total: int) -> None:
        prefix = self._paint(name, FILENAME) + self._paint(":", SEPARATOR) if self._filenames else ""
        self._out.write(f"{prefix}{total}\n")

    def filename(self, name: str) -> None:
        self._out.write(self._paint(name, FILENAME) + "\n")

    def _body(self, line: Line) -> str:
        if self._highlight and line.explanation is not None and line.explanation.matched:
            return line.explanation.highlight(line.text, MATCH, RESET)
        return line.text

    def _paint(self, text: str, code: Optional[str]) -> str:
        return f"{code}{text}{RESET}" if self._color and code else text
