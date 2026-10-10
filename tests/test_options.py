import unittest

from boolean_query_parser import QuerySyntaxError, apply_query, parse_query


class AllowRegexTests(unittest.TestCase):
    def test_regex_terms_are_rejected_when_disabled(self):
        with self.assertRaises(QuerySyntaxError) as caught:
            parse_query("error /x+/", allow_regex=False)
        self.assertEqual(caught.exception.position, 6)
        self.assertIn("disabled", str(caught.exception))

    def test_quoted_slashes_are_still_literal_text(self):
        self.assertTrue(apply_query(parse_query('"/x+/"', allow_regex=False), "path /x+/ here"))

    def test_everything_else_still_works(self):
        query = parse_query('error num:>3 "took {num:<5} ms" NOT warn*', allow_regex=False)
        self.assertTrue(apply_query(query, "error 9 took 2 ms"))


class WholeWordTests(unittest.TestCase):
    def match(self, query, text, **options):
        return apply_query(parse_query(query, whole_words=True, **options), text)

    def test_terms_must_be_whole_words(self):
        self.assertFalse(self.match("python", "pythonic code"))
        self.assertTrue(self.match("python", "I love python!"))
        self.assertTrue(self.match("python", "python"))

    def test_phrases_and_punctuated_terms(self):
        self.assertFalse(self.match('"hello world"', "say hello worlds"))
        self.assertTrue(self.match('"hello world"', "say hello world."))
        self.assertTrue(self.match("C++", "I use C++ daily"))
        self.assertFalse(self.match("C++", "C++x"))

    def test_combines_with_ignore_case(self):
        self.assertTrue(self.match("PYTHON", "python rocks", ignore_case=True))

    def test_default_is_substring(self):
        self.assertTrue(apply_query(parse_query("python"), "pythonic"))


class WildcardTests(unittest.TestCase):
    def test_star_matches_word_characters(self):
        cases = [
            ("pyth*", "pythonic", True),
            ("py*n", "pylon", True),
            ("py*n", "py n", False),
            ("*thon", "jython", True),
        ]
        for query, text, expected in cases:
            with self.subTest(query=query, text=text):
                self.assertIs(apply_query(parse_query(query, whole_words=True), text), expected)

    def test_wildcards_respect_whole_words(self):
        self.assertFalse(apply_query(parse_query("pyth*", whole_words=True), "xpython"))
        self.assertTrue(apply_query(parse_query("pyth*"), "xpython"))

    def test_quoted_star_is_literal(self):
        self.assertFalse(apply_query(parse_query('"py*"'), "pyx"))
        self.assertTrue(apply_query(parse_query('"py*"'), "a py* b"))

    def test_lone_star_is_still_an_error(self):
        with self.assertRaises(QuerySyntaxError):
            parse_query("a * b")


if __name__ == "__main__":
    unittest.main()
