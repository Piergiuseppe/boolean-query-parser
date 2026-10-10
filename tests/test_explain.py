import unittest

from boolean_query_parser import Hit, explain_query, parse_query


def explain(query, data, **options):
    return explain_query(parse_query(query, **options), data)


class ExplainTextTests(unittest.TestCase):
    def test_hits_cover_the_terms_that_made_it_match(self):
        text = "python with flask and 150 users"
        explanation = explain("python NOT java (flask OR num:>100)", text)
        self.assertTrue(explanation.matched)
        self.assertEqual(
            explanation.hits(),
            [Hit(None, 0, 6), Hit(None, 12, 17), Hit(None, 22, 25)],
        )
        self.assertEqual(explanation.highlight(text), "[python] with [flask] and [150] users")

    def test_negated_terms_and_failed_branches_are_not_hits(self):
        self.assertEqual(explain("a OR NOT zz", "a b").hits(), [Hit(None, 0, 1)])
        self.assertEqual(explain("zz OR NOT b", "a").hits(), [])

    def test_a_failed_query_has_no_hits_but_explains_why(self):
        explanation = explain("python java", "python only")
        self.assertFalse(explanation.matched)
        self.assertEqual(explanation.hits(), [])
        self.assertEqual(
            explanation.render(),
            "✗ AND\n  ✓ Text('python')  at 0-6\n  ✗ Text('java')",
        )

    def test_every_occurrence_is_reported(self):
        self.assertEqual(explain("ab", "ab ab").highlight("ab ab", "<", ">"), "<ab> <ab>")

    def test_templates_report_only_accepted_candidates(self):
        text = "took 12 ms and took 80 ms"
        self.assertEqual(explain('"took {num:<50} ms"', text).highlight(text), "[took 12 ms] and took 80 ms")

    def test_overlapping_hits_merge_when_highlighting(self):
        self.assertEqual(explain("abc bcd", "abcd").highlight("abcd"), "[abcd]")

    def test_empty_term_matches_without_hits(self):
        explanation = explain('""', "abc")
        self.assertTrue(explanation.matched)
        self.assertEqual(explanation.highlight("abc"), "abc")

    def test_honours_options(self):
        text = "Python and pythonic"
        explanation = explain("python", text, ignore_case=True, whole_words=True)
        self.assertEqual(explanation.highlight(text), "[Python] and pythonic")

    def test_explanation_agrees_with_matching(self):
        from boolean_query_parser import apply_query

        queries = ["a b", "a OR NOT b", '(x OR "y z") num:>3', "dur:>1s OR size:<1KB"]
        texts = ["a b", "b", "y z 5", "x 2", "took 2s", "10 B", ""]
        for query in queries:
            for text in texts:
                with self.subTest(query=query, text=text):
                    self.assertEqual(
                        explain(query, text).matched, apply_query(parse_query(query), text)
                    )


class ExplainRecordTests(unittest.TestCase):
    def test_hits_name_their_field(self):
        explanation = explain("title:python django", {"title": "python tips", "body": "use django"})
        self.assertEqual(explanation.hits(), [Hit("title", 0, 6), Hit(None, 16, 22)])

    def test_missing_field_is_explained_as_a_miss(self):
        explanation = explain("title:python", {"body": "python"})
        self.assertFalse(explanation.matched)
        self.assertEqual(explanation.render(), "✗ title:")

    def test_rejects_batches(self):
        with self.assertRaises(TypeError):
            explain("a", ["a"])


if __name__ == "__main__":
    unittest.main()
