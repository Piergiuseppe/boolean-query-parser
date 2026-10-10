import unittest

from boolean_query_parser import QueryError, apply_query, parse_query


class TestComparisonOperators(unittest.TestCase):
    """Test cases for comparison operators (num:>value, date:<=value, etc.).

    The field name is a TYPE selector:
      - num  → scans the text for numbers
      - date → scans the text for date patterns (YYYY-MM-DD, YYYY/MM/DD)
    The text is natural — no special 'field:value' markup required.
    """

    # ── Integer comparisons ───────────────────────────────────────────

    def test_greater_than_integer(self):
        """Test num:> with plain integer in text."""
        query = parse_query("num:>3")
        self.assertTrue(apply_query(query, "found 5 errors"))
        self.assertFalse(apply_query(query, "found 3 errors"))
        self.assertFalse(apply_query(query, "found 1 error"))

    def test_less_than_integer(self):
        """Test num:< with integers."""
        query = parse_query("num:<10")
        self.assertTrue(apply_query(query, "retry 5 of 20"))   # 5 < 10
        self.assertFalse(apply_query(query, "processed 10 items"))  # 10 not < 10
        self.assertFalse(apply_query(query, "handled 15 requests"))

    def test_greater_equal_integer(self):
        """Test num:>= with integers."""
        query = parse_query("num:>=5")
        self.assertTrue(apply_query(query, "score 5 points"))
        self.assertTrue(apply_query(query, "score 10 points"))
        self.assertFalse(apply_query(query, "score 4 points"))

    def test_less_equal_integer(self):
        """Test num:<= with integers."""
        query = parse_query("num:<=5")
        self.assertTrue(apply_query(query, "level 5 reached"))
        self.assertTrue(apply_query(query, "level 3 reached"))
        self.assertFalse(apply_query(query, "level 6 reached"))

    def test_equal_integer(self):
        """Test num:= with integers."""
        query = parse_query("num:=5")
        self.assertTrue(apply_query(query, "exit code 5"))
        self.assertFalse(apply_query(query, "exit code 3"))
        self.assertFalse(apply_query(query, "exit code 6"))

    # ── Float comparisons ─────────────────────────────────────────────

    def test_greater_than_float(self):
        """Test num:> with float values in text."""
        query = parse_query("num:>9.99")
        self.assertTrue(apply_query(query, "price is 15.50 dollars"))
        self.assertFalse(apply_query(query, "price is 9.99 dollars"))
        self.assertFalse(apply_query(query, "price is 5.00 dollars"))

    def test_less_equal_float(self):
        """Test num:<= with float values."""
        query = parse_query("num:<=100.50")
        self.assertTrue(apply_query(query, "total 100.50 EUR"))
        self.assertTrue(apply_query(query, "total 50.00 EUR"))
        self.assertFalse(apply_query(query, "total 100.51 EUR"))

    def test_float_in_query_int_in_text(self):
        """Float threshold in query vs integer in text."""
        query = parse_query("num:>2.5")
        self.assertTrue(apply_query(query, "scored 3 goals"))
        self.assertFalse(apply_query(query, "scored 2 goals"))

    def test_int_in_query_float_in_text(self):
        """Integer threshold in query vs float in text."""
        query = parse_query("num:>2")
        self.assertTrue(apply_query(query, "measured 2.5 cm"))
        self.assertFalse(apply_query(query, "measured 1.5 cm"))

    # ── Negative numbers ──────────────────────────────────────────────

    def test_negative_threshold(self):
        """Test comparison with a negative number as the threshold."""
        query = parse_query("num:>-10")
        self.assertTrue(apply_query(query, "temperature -5 degrees"))
        self.assertTrue(apply_query(query, "temperature 0 degrees"))
        self.assertFalse(apply_query(query, "temperature -15 degrees"))

    def test_negative_number_in_text(self):
        """Test comparison when the text contains a negative number."""
        query = parse_query("num:<0")
        self.assertTrue(apply_query(query, "balance is -50 today"))
        self.assertFalse(apply_query(query, "balance is 100 today"))

    # ── Multiple numbers in text ──────────────────────────────────────

    def test_any_number_matches(self):
        """If text contains multiple numbers, any one matching is enough."""
        query = parse_query("num:>10")
        self.assertTrue(apply_query(query, "got 2 errors and 15 warnings"))  # 15 > 10
        self.assertFalse(apply_query(query, "got 2 errors and 5 warnings"))

    def test_no_numbers_in_text(self):
        """Comparison returns False if there are no numbers in the text."""
        query = parse_query("num:>3")
        self.assertFalse(apply_query(query, "no numbers here at all"))

    def test_numeric_range(self):
        """Two num: comparisons ANDed to form a range."""
        query = parse_query("num:>=5 AND num:<=10")
        self.assertTrue(apply_query(query, "score 7"))
        self.assertTrue(apply_query(query, "values 5 and 10"))
        self.assertFalse(apply_query(query, "just 4"))
        self.assertFalse(apply_query(query, "high 11"))

    # ── Date comparisons ──────────────────────────────────────────────

    def test_date_greater_than(self):
        """Test date:> with YYYY-MM-DD in natural text."""
        query = parse_query("date:>2023-01-01")
        self.assertTrue(apply_query(query, "deployed on 2023-06-15 successfully"))
        self.assertFalse(apply_query(query, "deployed on 2023-01-01 exactly"))
        self.assertFalse(apply_query(query, "deployed on 2022-12-31 late"))

    def test_date_less_equal(self):
        """Test date:<= with dates in text."""
        query = parse_query("date:<=2024-12-31")
        self.assertTrue(apply_query(query, "created 2024-06-15"))
        self.assertTrue(apply_query(query, "created 2024-12-31"))
        self.assertFalse(apply_query(query, "created 2025-01-01"))

    def test_date_equal(self):
        """Test date:= with exact date match."""
        query = parse_query("date:=2023-06-15")
        self.assertTrue(apply_query(query, "event on 2023-06-15 at noon"))
        self.assertFalse(apply_query(query, "event on 2023-06-16 at noon"))

    def test_date_slash_format_in_query(self):
        """Dates using YYYY/MM/DD in the query."""
        query = parse_query("date:>2023/01/01")
        self.assertTrue(apply_query(query, "log entry 2023-06-15 ok"))
        self.assertFalse(apply_query(query, "log entry 2022-12-31 old"))

    def test_date_slash_format_in_text(self):
        """Dates using YYYY/MM/DD in the text."""
        query = parse_query("date:>2023-01-01")
        self.assertTrue(apply_query(query, "log entry 2023/06/15 ok"))
        self.assertFalse(apply_query(query, "log entry 2022/12/31 old"))

    def test_date_range(self):
        """Two date comparisons ANDed to form a date range."""
        query = parse_query("date:>=2023-01-01 AND date:<=2023-12-31")
        self.assertTrue(apply_query(query, "published 2023-06-15"))
        self.assertTrue(apply_query(query, "published 2023-01-01"))
        self.assertTrue(apply_query(query, "published 2023-12-31"))
        self.assertFalse(apply_query(query, "published 2022-12-31"))
        self.assertFalse(apply_query(query, "published 2024-01-01"))

    def test_datetime_in_text(self):
        """Text contains a datetime; query uses a date threshold."""
        query = parse_query("date:>2023-01-01")
        self.assertTrue(apply_query(query, "logged at 2023-06-15T10:30:00"))
        self.assertFalse(apply_query(query, "logged at 2022-12-31T23:59:59"))

    def test_datetime_in_query(self):
        """Query uses a full datetime threshold."""
        query = parse_query('date:>"2023-01-01T00:00:00"')
        self.assertTrue(apply_query(query, "stamp 2023-06-15T10:30:00 info"))
        self.assertFalse(apply_query(query, "stamp 2022-12-31T23:59:59 info"))

    def test_no_dates_in_text(self):
        """Comparison returns False if there are no dates in the text."""
        query = parse_query("date:>2023-01-01")
        self.assertFalse(apply_query(query, "no dates here at all"))

    def test_multiple_dates_any_match(self):
        """If text has multiple dates, any match is enough."""
        query = parse_query("date:>2024-01-01")
        self.assertTrue(apply_query(query, "from 2023-06-01 to 2024-06-15"))  # second date matches
        self.assertFalse(apply_query(query, "from 2022-01-01 to 2023-12-31"))

    # ── Combined with boolean operators ───────────────────────────────

    def test_comparison_with_and_text(self):
        """Comparison combined with AND and text matching."""
        query = parse_query("Error AND num:>3")
        self.assertTrue(apply_query(query, "Error: found 5 issues"))
        self.assertFalse(apply_query(query, "Warning: found 5 issues"))
        self.assertFalse(apply_query(query, "Error: found 2 issues"))

    def test_comparison_with_or(self):
        """Comparison combined with OR."""
        query = parse_query("num:>100 OR critical")
        self.assertTrue(apply_query(query, "requests 200 total"))
        self.assertTrue(apply_query(query, "critical failure"))
        self.assertFalse(apply_query(query, "requests 50 total"))

    def test_comparison_with_not(self):
        """NOT applied to a comparison."""
        query = parse_query("NOT num:=0")
        self.assertTrue(apply_query(query, "exit code 1"))
        self.assertFalse(apply_query(query, "exit code 0"))

    def test_comparison_with_parentheses(self):
        """Comparisons inside parenthesized groups."""
        query = parse_query("(num:=200 OR num:=201) AND NOT error")
        self.assertTrue(apply_query(query, "status 200 ok"))
        self.assertTrue(apply_query(query, "status 201 created"))
        self.assertFalse(apply_query(query, "status 200 error"))
        self.assertFalse(apply_query(query, "status 500 error"))

    def test_comparison_with_regex(self):
        """Mix comparison with regex patterns."""
        query = parse_query('(/error/i OR /warn/i) AND num:>=3')
        self.assertTrue(apply_query(query, "ERROR severity 5"))
        self.assertTrue(apply_query(query, "WARN severity 3"))
        self.assertFalse(apply_query(query, "ERROR severity 1"))
        self.assertFalse(apply_query(query, "INFO severity 5"))

    def test_complex_boolean_with_comparisons(self):
        """Complex expression mixing text, regex, comparisons, and all operators."""
        query = parse_query(
            '(num:>=3 AND /error|fatal/i) OR (num:>500 AND NOT maintenance)'
        )
        self.assertTrue(apply_query(query, "level 5 FATAL crash"))
        self.assertTrue(apply_query(query, "code 503 server down"))
        self.assertFalse(apply_query(query, "code 503 maintenance mode"))
        self.assertFalse(apply_query(query, "level 1 error minor"))

    def test_num_and_date_together(self):
        """Combine num: and date: in the same query."""
        query = parse_query("date:>2024-01-01 AND num:>=3")
        self.assertTrue(apply_query(query, "on 2024-06-15 we found 5 issues"))
        self.assertFalse(apply_query(query, "on 2024-06-15 we found 1 issue"))
        self.assertFalse(apply_query(query, "on 2023-06-15 we found 5 issues"))

    # ── Implicit AND with comparisons ─────────────────────────────────

    def test_implicit_and_text_and_comparison(self):
        """Implicit AND between text and comparison."""
        query = parse_query("error num:>5")
        self.assertTrue(apply_query(query, "error count 10"))
        self.assertFalse(apply_query(query, "warning count 10"))
        self.assertFalse(apply_query(query, "error count 2"))

    def test_implicit_and_two_comparisons(self):
        """Implicit AND between two comparisons."""
        query = parse_query("num:>3 num:<10")
        self.assertTrue(apply_query(query, "result 5"))
        self.assertFalse(apply_query(query, "result 2"))
        self.assertFalse(apply_query(query, "result 15"))

    def test_implicit_and_comparison_and_regex(self):
        """Implicit AND between comparison and regex."""
        query = parse_query('num:>0 /[A-Z]+/')
        self.assertTrue(apply_query(query, "count 5 HELLO"))
        self.assertFalse(apply_query(query, "count 5 hello"))
        self.assertFalse(apply_query(query, "count 0 HELLO"))

    # ── Quoted values in query ────────────────────────────────────────

    def test_quoted_date_in_comparison(self):
        """Quoted date value in comparison query."""
        query = parse_query('date:>"2023-01-01"')
        self.assertTrue(apply_query(query, "deployed 2023-06-15"))
        self.assertFalse(apply_query(query, "deployed 2022-12-31"))

    def test_single_quoted_date_in_comparison(self):
        """Single-quoted date value in comparison query."""
        query = parse_query("date:>'2023-01-01'")
        self.assertTrue(apply_query(query, "deployed 2023-06-15"))
        self.assertFalse(apply_query(query, "deployed 2022-12-31"))

    # ── List filtering ────────────────────────────────────────────────

    def test_list_filtering_with_num(self):
        """Filter a list of texts using num: comparison."""
        query = parse_query("num:>3 AND NOT critical")
        texts = [
            "event 5 normal",
            "event 2 normal",
            "event 10 critical",
            "event 8 warning",
            "no numbers here",
        ]
        expected = ["event 5 normal", "event 8 warning"]
        self.assertEqual(apply_query(query, texts), expected)

    def test_list_filtering_with_date(self):
        """Filter a list by date range."""
        query = parse_query("date:>=2023-06-01 AND date:<=2023-06-30")
        texts = [
            "event 2023-06-15 summer",
            "event 2023-05-31 spring",
            "event 2023-07-01 summer",
            "event 2023-06-01 start",
            "event 2023-06-30 end",
        ]
        expected = [
            "event 2023-06-15 summer",
            "event 2023-06-01 start",
            "event 2023-06-30 end",
        ]
        self.assertEqual(apply_query(query, texts), expected)

    # ── _compile matches evaluate ─────────────────────────────────────

    def test_compile_matches_evaluate(self):
        """Ensure compile() closure gives same results as evaluate()."""
        queries = [
            "num:>3",
            "num:<=100.50",
            "date:>=2023-01-01",
            "Error AND num:>5",
            "num:=200 OR num:=404",
            "NOT num:>=3",
            "(num:>0 AND num:<100) OR critical",
            "date:>2024-01-01 AND num:>=3",
        ]
        texts = [
            "Error 10 items 50.00 total 2024-01-15 status 200 severity 5",
            "info 2 items 200.00 total 2022-06-01 status 404 severity 1",
            "debug 5 items 100.50 total 2023-01-01 status 500 severity 3",
            "Error code 1 price 9.99",
            "critical event with no numbers or dates",
            "nothing special at all",
        ]
        for qs in queries:
            q = parse_query(qs)
            closure = q.compile()
            for t in texts:
                self.assertEqual(
                    q.evaluate(t),
                    closure(t),
                    msg=f"Mismatch for query={qs!r}, text={t!r}"
                )

    # ── Edge cases / error handling ───────────────────────────────────

    def test_no_matching_values_in_text(self):
        """num: comparison on text without any numbers → False."""
        query = parse_query("num:>5")
        self.assertFalse(apply_query(query, "just words no digits"))

    def test_comparison_without_value_raises(self):
        """num:> with nothing after the operator is a syntax error."""
        with self.assertRaises(QueryError):
            parse_query("num:>")

    def test_unknown_field_type_raises(self):
        """Using an unknown field type (not num/date) raises an error."""
        with self.assertRaises(QueryError):
            parse_query("foo:>5")

    def test_invalid_date_value_raises(self):
        """date:>invalid raises an error at parse time."""
        with self.assertRaises(QueryError):
            parse_query("date:>notadate")

    def test_invalid_num_value_raises(self):
        """num:>abc raises an error at parse time."""
        with self.assertRaises(QueryError):
            parse_query("num:>abc")

    def test_colon_without_operator_is_a_field_that_plain_text_rejects(self):
        query = parse_query("field:text")
        with self.assertRaises(QueryError):
            apply_query(query, "field:text")
        with self.assertRaises(QueryError):
            parse_query("num:")

    def test_comparison_repr(self):
        """Verify __repr__ of ComparisonNode."""
        query = parse_query("num:>3")
        self.assertIn("Comparison", repr(query))

    def test_comparison_in_large_list(self):
        """Filter a large list using comparisons for performance check."""
        query = parse_query("num:>=50 AND NOT failed")
        texts = []
        expected = []
        for i in range(5000):
            if i % 3 == 0:
                t = f"test score {i} passed"
                texts.append(t)
                if i >= 50:
                    expected.append(t)
            elif i % 3 == 1:
                texts.append(f"test score {i} failed")
            else:
                texts.append("no numbers here")
        result = apply_query(query, texts)
        self.assertEqual(result, expected)

    def test_number_embedded_in_word_not_matched_as_date(self):
        """Numbers that look like they could be part of something shouldn't confuse date."""
        query = parse_query("date:>2023-01-01")
        # Text with numbers but no date pattern
        self.assertFalse(apply_query(query, "version 2023 build 105"))

    def test_adjacent_numbers_each_checked(self):
        """Multiple numbers separated by text are each checked independently."""
        query = parse_query("num:=42")
        self.assertTrue(apply_query(query, "the answer is 42 not 43"))
        self.assertFalse(apply_query(query, "values are 41 and 43"))


class NumberScanningTests(unittest.TestCase):
    def test_hyphen_after_a_word_is_not_a_minus_sign(self):
        query = parse_query("num:<0")
        for text in ("pages 3-7", "item-5", "a_-5", "v1.-2"):
            with self.subTest(text=text):
                self.assertFalse(apply_query(query, text))

    def test_minus_after_space_or_symbol_is_a_sign(self):
        query = parse_query("num:<0")
        for text in ("temp -5 C", "(-5)", "=-5", "-5"):
            with self.subTest(text=text):
                self.assertTrue(apply_query(query, text))

    def test_numbers_inside_dates_and_times_are_skipped(self):
        query = parse_query("num:>9")
        self.assertFalse(apply_query(query, "at 2024-01-01 10:30:00"))
        self.assertFalse(apply_query(query, "at 2024/01/01T10:30"))
        self.assertTrue(apply_query(query, "at 2024-01-01 10:30:00 took 12"))


class DatePrecisionTests(unittest.TestCase):
    def test_date_only_threshold_compares_whole_days(self):
        stamp = "at 2023-01-01T10:00:00"
        self.assertTrue(apply_query(parse_query("date:=2023-01-01"), stamp))
        self.assertFalse(apply_query(parse_query("date:>2023-01-01"), stamp))
        self.assertTrue(apply_query(parse_query("date:<2023-01-02"), stamp))

    def test_threshold_with_time_compares_times(self):
        stamp = "at 2023-01-01T10:00:00"
        self.assertTrue(apply_query(parse_query("date:>2023-01-01T09:00"), stamp))
        self.assertFalse(apply_query(parse_query("date:>2023-01-01T10:00:00"), stamp))

    def test_space_separated_times_are_recognised(self):
        query = parse_query('date:>="2023-01-01 09:00"')
        self.assertTrue(apply_query(query, "log 2023-01-01 10:00 started"))
        self.assertFalse(apply_query(query, "log 2023-01-01 08:59 started"))

    def test_dates_glued_to_other_digits_are_ignored(self):
        query = parse_query("date:>2023-01-01")
        self.assertFalse(apply_query(query, "id 12023-05-05"))
        self.assertFalse(apply_query(query, "id 2023-05-051"))
        self.assertTrue(apply_query(query, "(2023-05-05)"))

    def test_impossible_dates_in_text_never_match(self):
        self.assertFalse(apply_query(parse_query("date:>2023-01-01"), "bad 2023-13-45"))


if __name__ == "__main__":
    unittest.main()
