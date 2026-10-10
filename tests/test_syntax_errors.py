import unittest

from boolean_query_parser import QueryError, QuerySyntaxError, parse_query
from boolean_query_parser.syntax import MAX_DEPTH


class SyntaxErrorTests(unittest.TestCase):
    def assertSyntaxError(self, query, message, position):
        with self.assertRaises(QuerySyntaxError) as caught:
            parse_query(query)
        self.assertIn(message, str(caught.exception))
        self.assertEqual(caught.exception.position, position)

    def test_is_a_query_error_and_a_value_error(self):
        self.assertTrue(issubclass(QuerySyntaxError, QueryError))
        self.assertTrue(issubclass(QuerySyntaxError, ValueError))

    def test_dangling_operators_name_the_operator(self):
        self.assertSyntaxError("NOT", "Unexpected end of query after 'NOT'", 3)
        self.assertSyntaxError("a AND", "Unexpected end of query after 'AND'", 5)
        self.assertSyntaxError("a OR", "Unexpected end of query after 'OR'", 4)

    def test_unexpected_tokens(self):
        self.assertSyntaxError("a AND b)", "Unexpected token ')' at position 7", 7)
        self.assertSyntaxError("a AND OR b", "Unexpected token 'OR' at position 6", 6)

    def test_missing_parenthesis(self):
        self.assertSyntaxError("x (a", "Missing closing parenthesis", 2)

    def test_empty_query(self):
        self.assertSyntaxError("  ", "Empty query", 0)

    def test_invalid_terms_point_at_the_term(self):
        self.assertSyntaxError("a (b /[/)", "Invalid regular expression", 5)
        self.assertSyntaxError("a /x/g", "Unsupported regex flag(s) 'g'", 2)
        self.assertSyntaxError("a foo:>3", "Unknown comparison type 'foo'", 2)
        self.assertSyntaxError("a num:>x", "Invalid numeric value", 2)
        self.assertSyntaxError("a date:>2023-13-45", "Invalid date value", 2)
        self.assertSyntaxError('a "{num:>x}"', "Invalid numeric value", 2)

    def test_nesting_is_limited_instead_of_overflowing_the_stack(self):
        allowed = "(" * MAX_DEPTH + "a" + ")" * MAX_DEPTH
        self.assertIsNotNone(parse_query(allowed))
        self.assertSyntaxError("(" * 5000 + "a" + ")" * 5000, "nests deeper than", MAX_DEPTH)
        with self.assertRaises(QuerySyntaxError):
            parse_query("NOT " * 5000 + "a")

    def test_query_must_be_a_string(self):
        with self.assertRaises(TypeError):
            parse_query(None)


if __name__ == "__main__":
    unittest.main()
