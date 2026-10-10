import unittest

import boolean_query_parser
from boolean_query_parser import apply_query, parse_query


class ApplyQueryInputTests(unittest.TestCase):
    def setUp(self):
        self.query = parse_query("py")

    def test_any_iterable_of_strings_is_filtered_in_order(self):
        self.assertEqual(apply_query(self.query, ("py", "rb", "py2")), ["py", "py2"])
        self.assertEqual(apply_query(self.query, (t for t in ["rb", "py"])), ["py"])
        self.assertEqual(apply_query(self.query, iter(["py"])), ["py"])

    def test_rejects_non_text_inputs(self):
        for data in (42, None, b"py", bytearray(b"py")):
            with self.subTest(data=data):
                with self.assertRaises(TypeError):
                    apply_query(self.query, data)

    def test_rejects_non_string_items(self):
        for items in (["py", None], ["py", 3], [["py"]]):
            with self.subTest(items=items):
                with self.assertRaises(TypeError):
                    apply_query(self.query, items)

    def test_rejects_non_string_items_with_ignore_case(self):
        with self.assertRaises(TypeError):
            apply_query(parse_query("py", ignore_case=True), ["py", 3])


class IgnoreCaseTests(unittest.TestCase):
    def test_default_is_case_sensitive(self):
        self.assertFalse(apply_query(parse_query("Python"), "python"))

    def test_applies_to_every_kind_of_term(self):
        cases = [
            ("Python", "i like PYTHON"),
            ('"Hello World"', "hello world"),
            ("/pyth.n/", "PYTHON"),
            ('"Took {num:<50} MS"', "took 12 ms"),
            ("CAFÉ", "café"),
        ]
        for query, text in cases:
            with self.subTest(query=query):
                self.assertTrue(apply_query(parse_query(query, ignore_case=True), text))

    def test_negation_still_works(self):
        query = parse_query("error NOT Timeout", ignore_case=True)
        self.assertTrue(apply_query(query, "ERROR disk full"))
        self.assertFalse(apply_query(query, "ERROR timeout"))


class LongQueryTests(unittest.TestCase):
    def test_long_chains_evaluate_without_recursion(self):
        terms = [f"w{i}" for i in range(20000)]
        every = parse_query(" ".join(terms))
        some = parse_query(" OR ".join(terms))
        self.assertFalse(apply_query(every, "w1 w2"))
        self.assertTrue(apply_query(every, " ".join(terms)))
        self.assertEqual(apply_query(some, ["w19999", "zzz"]), ["w19999"])

    def test_chains_are_flattened(self):
        self.assertEqual(
            repr(parse_query("a b AND c OR d OR (e OR f)")),
            "((Text('a') AND Text('b') AND Text('c')) OR Text('d') OR Text('e') OR Text('f'))",
        )

    def test_evaluate_matches_compile(self):
        query = parse_query("(a OR b) c NOT d")
        predicate = query.compile()
        for text in ["a c", "b c d", "c", "a b c"]:
            self.assertEqual(query.evaluate(text), predicate(text))


class PackageTests(unittest.TestCase):
    def test_legacy_module_path_still_imports(self):
        from boolean_query_parser.parser import Lexer, Parser, QueryError, apply_query, parse_query

        tree = Parser(Lexer("a OR b").tokenize()).parse()
        self.assertTrue(apply_query(tree, "b"))
        self.assertTrue(issubclass(QueryError, Exception))
        self.assertTrue(callable(parse_query))

    def test_exposes_a_version(self):
        self.assertIsInstance(boolean_query_parser.__version__, str)


if __name__ == "__main__":
    unittest.main()
