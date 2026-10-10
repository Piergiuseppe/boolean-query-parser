from __future__ import annotations

import argparse
import os
import sys
from contextlib import contextmanager
from typing import IO, Iterator, Optional, Sequence

from ..exceptions import QueryError
from ..options import QueryOptions
from ..services import ParsingService
from .output import Printer
from .search import LineSearch

SELECTED, NOTHING_SELECTED, TROUBLE = 0, 1, 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bqp",
        description="Print the lines that match a boolean query, like grep.",
        epilog="Exit status is 0 if a line was selected, 1 if none was, 2 on errors.",
    )
    parser.add_argument("query", help="the boolean query, e.g. 'error AND num:>500 NOT healthcheck'")
    parser.add_argument("files", nargs="*", default=["-"], help="files to search; '-' or nothing reads stdin")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="match terms regardless of case")
    parser.add_argument("-w", "--whole-words", action="store_true", help="match terms only as whole words")
    parser.add_argument("--no-regex", action="store_true", help="reject /regex/ terms in the query")
    parser.add_argument("-v", "--invert-match", action="store_true", help="select the lines that do not match")
    parser.add_argument("-c", "--count", action="store_true", help="print only how many lines each file selected")
    parser.add_argument(
        "-l", "--files-with-matches", action="store_true", help="print only the names of files with a selected line"
    )
    parser.add_argument("-n", "--line-number", action="store_true", help="prefix lines with their line number")
    parser.add_argument(
        "-H", "--with-filename", action="store_true", default=None, help="prefix lines with the file name"
    )
    parser.add_argument(
        "--no-filename", dest="with_filename", action="store_false", help="never prefix lines with the file name"
    )
    parser.add_argument(
        "--json", action="store_true", help="read each line as a JSON object, so field:term queries work"
    )
    parser.add_argument("--explain", action="store_true", help="print why each selected line matched")
    parser.add_argument(
        "--color", choices=("auto", "always", "never"), default="auto", help="highlight the matching terms"
    )
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    stdin: Optional[IO[str]] = None,
    stdout: Optional[IO[str]] = None,
    stderr: Optional[IO[str]] = None,
) -> int:
    if stdin is None:
        stdin = sys.stdin
        if hasattr(stdin, "reconfigure"):
            stdin.reconfigure(errors="replace")
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    args = build_parser().parse_args(argv)
    try:
        query = ParsingService().parse(
            args.query,
            QueryOptions(
                ignore_case=args.ignore_case, whole_words=args.whole_words, allow_regex=not args.no_regex
            ),
        )
    except QueryError as error:
        stderr.write(f"bqp: {error}\n")
        return TROUBLE

    color = args.color == "always" or (args.color == "auto" and stdout.isatty() and not args.json)
    try:
        search = LineSearch(
            query,
            records=args.json,
            invert=args.invert_match,
            explain=args.explain or (color and not args.json and not args.invert_match),
        )
    except QueryError as error:
        stderr.write(f"bqp: {error}. Pass --json to search JSON lines by field.\n")
        return TROUBLE
    printer = Printer(
        stdout,
        color=color,
        # Hits in a record point into its values, not into the raw JSON line.
        highlight=color and not args.json,
        line_numbers=args.line_number,
        filenames=args.with_filename if args.with_filename is not None else len(args.files) > 1,
        explain=args.explain,
    )

    try:
        return _search_all(args, stdin, stderr, search, printer)
    except BrokenPipeError:
        _silence(stdout)
        return SELECTED


def _search_all(args, stdin: IO[str], stderr: IO[str], search: LineSearch, printer: Printer) -> int:
    problems = []
    selected_any = False
    for name in args.files:
        label = "(standard input)" if name == "-" else name

        def skip(reason: str, label: str = label) -> None:
            problems.append(reason)
            stderr.write(f"bqp: {label}: {reason}\n")

        try:
            with _open(name, stdin) as stream:
                selected_any |= _search_one(label, stream, search, printer, args, skip)
        except BrokenPipeError:
            raise
        except OSError as error:
            skip(error.strerror or str(error))
    if problems:
        return TROUBLE
    return SELECTED if selected_any else NOTHING_SELECTED


def _search_one(label: str, stream: IO[str], search: LineSearch, printer: Printer, args, skip) -> bool:
    total = 0
    for line in search.selected(stream, skip):
        total += 1
        if args.files_with_matches:
            printer.filename(label)
            return True
        if not args.count:
            printer.line(label, line)
    if args.count and not args.files_with_matches:
        printer.count(label, total)
    return total > 0


def _silence(stdout: IO[str]) -> None:
    # The reader went away (e.g. `| head`): stop quietly, and keep Python's
    # shutdown flush from raising again on the closed pipe.
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stdout.fileno())
    except (OSError, ValueError, AttributeError):
        pass


@contextmanager
def _open(name: str, stdin: IO[str]) -> Iterator[IO[str]]:
    if name == "-":
        yield stdin
        return
    with open(name, encoding="utf-8", errors="replace") as stream:
        yield stream
