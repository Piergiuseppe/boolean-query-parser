import unittest

from boolean_query_parser import QueryError, QuerySyntaxError, apply_query, parse_query

DOCS = [
    {"title": "Python tips", "body": "use django", "meta": {"author": "ann", "views": 1500}, "tags": ["web", "py"]},
    {"title": "Rust", "body": "python is slow", "meta": {"author": "bob", "views": 20}, "tags": []},
    {"title": "Go", "published": True, "meta.author": "literal key"},
]


def titles(query, **options):
    return [doc["title"] for doc in apply_query(parse_query(query, **options), DOCS)]


class FieldQueryTests(unittest.TestCase):
    def test_scoped_and_unscoped_terms(self):
        self.assertEqual(titles("title:Python"), ["Python tips"])
        self.assertEqual(titles("python", ignore_case=True), ["Python tips", "Rust"])
        self.assertEqual(titles("title:python", ignore_case=True), ["Python tips"])

    def test_field_values_of_any_shape(self):
        self.assertEqual(titles("meta.views:num:>100"), ["Python tips"])
        self.assertEqual(titles("tags:web"), ["Python tips"])
        self.assertEqual(titles("published:true"), ["Go"])

    def test_dotted_names_prefer_a_literal_key(self):
        self.assertEqual(titles("meta.author:ann"), ["Python tips"])
        self.assertEqual(titles('meta.author:"literal key"'), ["Go"])

    def test_every_kind_of_term_can_be_scoped(self):
        self.assertEqual(titles("title:(Rust OR Go)"), ["Rust", "Go"])
        self.assertEqual(titles('title:"Python tips"'), ["Python tips"])
        self.assertEqual(titles("title:/^py/i"), ["Python tips"])
        self.assertEqual(titles("title:Pyth*"), ["Python tips"])
        self.assertEqual(titles("title: Rust"), ["Rust"])

    def test_missing_fields_never_match(self):
        self.assertEqual(titles("missing:x"), [])
        self.assertEqual(titles("NOT missing:x"), ["Python tips", "Rust", "Go"])
        self.assertEqual(titles("NOT title:Rust"), ["Python tips", "Go"])

    def test_a_single_mapping_returns_a_bool(self):
        self.assertTrue(apply_query(parse_query("body:django"), DOCS[0]))
        self.assertFalse(apply_query(parse_query("body:django"), DOCS[1]))

    def test_any_iterable_of_mappings(self):
        query = parse_query("title:Go")
        self.assertEqual(apply_query(query, (doc for doc in DOCS)), [DOCS[2]])


class FieldErrorTests(unittest.TestCase):
    def test_fields_need_records(self):
        with self.assertRaises(QueryError):
            apply_query(parse_query("title:x"), "title:x")

    def test_fields_cannot_nest(self):
        with self.assertRaises(QuerySyntaxError):
            parse_query("a:(b:x)")

    def test_a_field_with_an_operator_suggests_a_kind(self):
        with self.assertRaises(QuerySyntaxError) as caught:
            parse_query("price:>5")
        self.assertIn("price:num:>5", str(caught.exception))

    def test_batches_must_not_mix_texts_and_mappings(self):
        for items in (["a", {"a": 1}], [{"a": 1}, None]):
            with self.subTest(items=items):
                with self.assertRaises(TypeError):
                    apply_query(parse_query("a"), items)


if __name__ == "__main__":
    unittest.main()
