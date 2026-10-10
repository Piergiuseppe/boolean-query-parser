import io
import time
import unittest

from boolean_query_parser import QuerySyntaxError, apply_query, explain_query, parse_query
from boolean_query_parser.cli import main


class WildcardSafetyTests(unittest.TestCase):
    def test_many_stars_stay_fast_on_failing_input(self):
        for query, text in (("a********b", "a" * 40 + "c"), ("a*a*a*a*a*a*b", "a" * 50000)):
            with self.subTest(query=query):
                started = time.perf_counter()
                self.assertFalse(apply_query(parse_query(query, allow_regex=False), text))
                self.assertLess(time.perf_counter() - started, 2)

    def test_special_characters_around_stars_are_literal(self):
        self.assertTrue(apply_query(parse_query("C++*"), "C++11"))
        self.assertTrue(apply_query(parse_query("a.b*"), "a.bc"))
        self.assertFalse(apply_query(parse_query("a.b*"), "axbc"))

    def test_highlight_agrees_with_case_insensitive_matching(self):
        explanation = explain_query(parse_query("CAFÉ", ignore_case=True), "un café")
        self.assertTrue(explanation.matched)
        self.assertEqual(explanation.highlight("un café"), "un [café]")


class ExactQuantityTests(unittest.TestCase):
    def test_conversions_do_not_lose_precision(self):
        self.assertTrue(apply_query(parse_query("dur:=1.1ms"), "took 1100us"))
        self.assertTrue(apply_query(parse_query("dur:>=1.1ms"), "took 1100us"))
        self.assertTrue(apply_query(parse_query("size:=1.1kb"), "1100 B"))

    def test_greek_mu_is_a_microsecond(self):
        self.assertTrue(apply_query(parse_query("dur:<1ms"), "took 5 μs"))


class RecordValueTests(unittest.TestCase):
    def test_floats_are_never_read_in_scientific_notation(self):
        self.assertFalse(apply_query(parse_query("num:>5"), {"v": 1e-07}))
        self.assertFalse(apply_query(parse_query("a:num:<5"), {"a": 1e20}))
        self.assertTrue(apply_query(parse_query("a:num:=0.5"), {"a": 0.5}))

    def test_invalid_field_names(self):
        for query in ("ti*:x", "AND:x", "not:x"):
            with self.subTest(query=query):
                with self.assertRaises(QuerySyntaxError):
                    parse_query(query)


class CliEdgeTests(unittest.TestCase):
    def run_cli(self, *argv, stdin=""):
        out, err = io.StringIO(), io.StringIO()
        status = main(list(argv), stdin=io.StringIO(stdin), stdout=out, stderr=err)
        return status, out.getvalue(), err.getvalue()

    def test_json_lines_are_not_highlighted(self):
        _, out, _ = self.run_cli("--json", "--color", "always", "a:foo", stdin='{"a":"foo"}\n')
        self.assertIn('{"a":"foo"}', out)
        self.assertNotIn("\033[1;31m", out)

    def test_files_with_matches_ignores_count(self):
        self.assertEqual(self.run_cli("-c", "-l", "zzz", stdin="foo\n"), (1, "", ""))

    def test_crlf_lines(self):
        self.assertEqual(self.run_cli("-w", "foo", stdin="foo\r\nbar\r\n")[1], "foo\n")


if __name__ == "__main__":
    unittest.main()
