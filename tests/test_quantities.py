import unittest

from boolean_query_parser import QuerySyntaxError, apply_query, parse_query


class DurationTests(unittest.TestCase):
    def test_compares_after_converting_units(self):
        cases = [
            ("dur:>1s", "took 1500ms", True),
            ("dur:>1s", "took 900ms", False),
            ("dur:<2min", "took 90 s", True),
            ("dur:>=1h", "uptime 3hours", True),
            ("dur:=1.5s", "took 1500ms", True),
            ("dur:<1ms", "took 250us", True),
            ('dur:>"1.5 s"', "took 2s", True),
        ]
        for query, text, expected in cases:
            with self.subTest(query=query, text=text):
                self.assertIs(apply_query(parse_query(query), text), expected)

    def test_units_must_stand_alone(self):
        query = parse_query("dur:>0s")
        for text in ("v1.5s", "5sec5", "id 3hx"):
            with self.subTest(text=text):
                self.assertFalse(apply_query(query, text))

    def test_threshold_needs_a_unit(self):
        for query in ("dur:>2", "dur:>2x", "dur:>ms"):
            with self.subTest(query=query):
                with self.assertRaises(QuerySyntaxError):
                    parse_query(query)


class SizeTests(unittest.TestCase):
    def test_decimal_and_binary_units(self):
        cases = [
            ("size:>10MB", "file 11MB", True),
            ("size:>10MB", "file 10MiB", True),
            ("size:<1kb", "got 512 bytes", True),
            ("size:>=1GiB", "disk 1024 MiB", True),
            ("size:>1KB", "file 1000 B", False),
        ]
        for query, text, expected in cases:
            with self.subTest(query=query, text=text):
                self.assertIs(apply_query(parse_query(query), text), expected)

    def test_units_ignore_case(self):
        self.assertTrue(apply_query(parse_query("size:>1mb"), "upload 2 Mb"))


class QuantityTemplateTests(unittest.TestCase):
    def test_placeholders(self):
        self.assertTrue(apply_query(parse_query('"took {dur:<1s}"'), "request took 250ms ok"))
        self.assertFalse(apply_query(parse_query('"took {dur:<1s}"'), "request took 2s ok"))
        self.assertTrue(apply_query(parse_query('"upload of {size:>1MB} done"'), "upload of 3 MB done"))


if __name__ == "__main__":
    unittest.main()
