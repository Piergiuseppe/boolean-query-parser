import unittest

from boolean_query_parser import QuerySyntaxError, apply_query, parse_query
from boolean_query_parser.syntax import Lexer, Token, TokenType


class MatchTable(unittest.TestCase):
    def assertMatches(self, cases, ignore_case=False):
        for query, text, expected in cases:
            with self.subTest(query=query, text=text):
                self.assertIs(apply_query(parse_query(query, ignore_case=ignore_case), text), expected)


class DateTimePrecisionTests(MatchTable):
    def test_minute_threshold_ignores_seconds(self):
        self.assertMatches([
            ("date:=2024-01-01T10:00", "at 2024-01-01 10:00:30", True),
            ("date:<=2024-01-01T10:00", "at 2024-01-01 10:00:30", True),
            ("date:>2024-01-01T10:00", "at 2024-01-01 10:00:30", False),
            ("date:>2024-01-01T10:00:00", "at 2024-01-01 10:00:30", True),
        ])

    def test_malformed_time_does_not_hide_the_date(self):
        self.assertMatches([
            ("date:=2024-01-01", "2024-01-01 99:99", True),
            ("date:=2024-01-01", "2024-01-01 10:001", True),
        ])


class TemplateBoundaryTests(MatchTable):
    def test_numbers_inside_dates_are_not_placeholders(self):
        self.assertMatches([
            ('"{num:=1}"', "2024-01-01", False),
            ('"{num:=10} x"', "2024-01-01 10:30 x", False),
            ('"{num:=5} x"', "on 2024-01-01 got 5 x", True),
        ])

    def test_dates_glued_to_digits_are_not_placeholders(self):
        self.assertMatches([
            ('"{date:=2024-01-01}"', "12024-01-01", False),
            ('"{date:=2024-01-01}"', "2024-01-015", False),
        ])

    def test_a_signed_number_is_never_read_without_its_sign(self):
        self.assertMatches([
            ('"{num:>0} degrees"', "-5 degrees", False),
            ('"{num:>0}"', "-5", False),
            ('"{num:<0} C"', "temp -5 C", True),
            ('"{num:=5} C"', "pages 3-5 C", True),
        ])

    def test_ignore_case_only_loosens_the_literal_text(self):
        self.assertMatches([
            ('"{date:=2024-01-01}"', "2024-01-01t10:00", True),
            ('"Took {num:<5} MS"', "took 3 ms", True),
        ], ignore_case=True)


class NumberEdgeTests(MatchTable):
    def test_digits_after_a_dot_are_not_a_new_number(self):
        self.assertMatches([
            ("num:=5", "cost .5", False),
            ("num:=3", "v1.2.3", False),
            ("num:=1.2", "v1.2.3", True),
        ])

    def test_huge_digit_runs_do_not_crash(self):
        self.assertMatches([
            ("num:>5", "1" * 5000, True),
            ('"{num:>5}"', "1" * 5000, True),
        ])

    def test_threshold_spellings(self):
        self.assertMatches([("num:>+5", "6", True), ("num:>.5", "x 1", True)])
        for query in ("num:>nan", "num:>inf", "num:>1_000"):
            with self.subTest(query=query):
                with self.assertRaises(QuerySyntaxError):
                    parse_query(query)


class RobustnessTests(unittest.TestCase):
    def test_regexes_the_engine_cannot_build_are_syntax_errors(self):
        for query in ("/a{99999999999}/", "/" + "(?:" * 2000 + "a" + ")" * 2000 + "/", "/a/i_x"):
            with self.subTest(query=query[:20]):
                with self.assertRaises(QuerySyntaxError):
                    parse_query(query)

    def test_tokens_compare_without_their_source(self):
        self.assertEqual(Token(TokenType.TEXT, "a", 0), Lexer("a").tokenize()[0])

    def test_legacy_compile_name_still_works(self):
        self.assertTrue(parse_query("a")._compile()("a"))


if __name__ == "__main__":
    unittest.main()
