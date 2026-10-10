import unittest

from boolean_query_parser import apply_query, parse_query


class TestTemplateComparisons(unittest.TestCase):
    """Test cases for positional template matching with {num:op} and {date:op} placeholders."""

    # ── basic number templates ──────────────────────────────────────────

    def test_basic_template_match(self):
        """Template matches number at the correct position."""
        query = parse_query('"evaluated in {num:<50} ms"')
        self.assertTrue(apply_query(query, "test 1 evaluated in 12 ms"))

    def test_basic_template_no_match(self):
        """Template rejects number that fails the comparison."""
        query = parse_query('"evaluated in {num:<50} ms"')
        self.assertFalse(apply_query(query, "test 1 evaluated in 80 ms"))

    def test_template_ignores_numbers_in_wrong_position(self):
        """Only the number between 'in' and 'ms' is checked, not '1' in 'test 1'."""
        query = parse_query('"test {num:>5} evaluated in {num:<50} ms"')
        # 10 > 5 ✓ and 12 < 50 ✓
        self.assertTrue(apply_query(query, "test 10 evaluated in 12 ms"))
        # 3 > 5 ✗
        self.assertFalse(apply_query(query, "test 3 evaluated in 12 ms"))
        # 10 > 5 ✓ but 150 < 50 ✗
        self.assertFalse(apply_query(query, "test 10 evaluated in 150 ms"))

    def test_template_exact_boundary(self):
        """Boundary value: num:<50 rejects exactly 50."""
        query = parse_query('"took {num:<50} ms"')
        self.assertTrue(apply_query(query, "took 49 ms"))
        self.assertFalse(apply_query(query, "took 50 ms"))

    def test_template_equal_operator(self):
        """Template with = operator matches exact number."""
        query = parse_query('"error code {num:=404}"')
        self.assertTrue(apply_query(query, "error code 404"))
        self.assertFalse(apply_query(query, "error code 500"))

    def test_template_gte_operator(self):
        """Template with >= operator."""
        query = parse_query('"score {num:>=80} points"')
        self.assertTrue(apply_query(query, "score 80 points"))
        self.assertTrue(apply_query(query, "score 95 points"))
        self.assertFalse(apply_query(query, "score 79 points"))

    def test_template_lte_operator(self):
        """Template with <= operator."""
        query = parse_query('"latency {num:<=100} ms"')
        self.assertTrue(apply_query(query, "latency 100 ms"))
        self.assertTrue(apply_query(query, "latency 42 ms"))
        self.assertFalse(apply_query(query, "latency 101 ms"))

    def test_template_gt_operator(self):
        """Template with > operator."""
        query = parse_query('"version {num:>2}"')
        self.assertTrue(apply_query(query, "version 3"))
        self.assertFalse(apply_query(query, "version 2"))

    def test_template_float_number(self):
        """Template with float comparison."""
        query = parse_query('"ratio {num:<1.5}"')
        self.assertTrue(apply_query(query, "ratio 1.2"))
        self.assertFalse(apply_query(query, "ratio 1.8"))

    def test_template_negative_number(self):
        """Template with negative number in text."""
        query = parse_query('"offset {num:<0}"')
        self.assertTrue(apply_query(query, "offset -5"))
        self.assertFalse(apply_query(query, "offset 3"))

    # ── date templates ──────────────────────────────────────────────────

    def test_template_date_match(self):
        """Template with date placeholder."""
        query = parse_query('"deployed on {date:>2023-01-01} successfully"')
        self.assertTrue(apply_query(query, "deployed on 2024-03-15 successfully"))
        self.assertFalse(apply_query(query, "deployed on 2022-12-01 successfully"))

    def test_template_date_lte(self):
        """Template with date <= comparison."""
        query = parse_query('"expires {date:<=2025-12-31}"')
        self.assertTrue(apply_query(query, "expires 2025-06-01"))
        self.assertFalse(apply_query(query, "expires 2026-01-01"))

    def test_template_date_equal(self):
        """Template with date = comparison."""
        query = parse_query('"released {date:=2024-01-15}"')
        self.assertTrue(apply_query(query, "released 2024-01-15"))
        self.assertFalse(apply_query(query, "released 2024-01-16"))

    # ── mixed num + date templates ──────────────────────────────────────

    def test_template_mixed_num_and_date(self):
        """Template with both num and date placeholders."""
        query = parse_query('"build {num:>100} on {date:>2024-01-01}"')
        self.assertTrue(apply_query(query, "build 250 on 2024-06-15"))
        self.assertFalse(apply_query(query, "build 50 on 2024-06-15"))
        self.assertFalse(apply_query(query, "build 250 on 2023-12-01"))

    # ── combined with boolean operators ─────────────────────────────────

    def test_template_and_text(self):
        """Template combined with AND text."""
        query = parse_query('"completed in {num:<50} ms" AND Success')
        self.assertTrue(apply_query(query, "Success completed in 12 ms"))
        self.assertFalse(apply_query(query, "Failure completed in 12 ms"))
        self.assertFalse(apply_query(query, "Success completed in 80 ms"))

    def test_template_or_text(self):
        """Template combined with OR."""
        query = parse_query('"latency {num:<10} ms" OR fast')
        self.assertTrue(apply_query(query, "latency 5 ms"))
        self.assertTrue(apply_query(query, "response was fast"))
        self.assertFalse(apply_query(query, "latency 20 ms slow"))

    def test_template_not(self):
        """NOT applied to a template."""
        query = parse_query('NOT "error code {num:=500}"')
        self.assertTrue(apply_query(query, "error code 200"))
        self.assertFalse(apply_query(query, "error code 500"))

    def test_template_in_parentheses(self):
        """Template inside parenthesized boolean expression."""
        query = parse_query('("took {num:<100} ms" OR "took {num:<100} s") AND Success')
        self.assertTrue(apply_query(query, "Success took 50 ms"))
        self.assertTrue(apply_query(query, "Success took 2 s"))
        self.assertFalse(apply_query(query, "Failure took 50 ms"))

    def test_template_implicit_and(self):
        """Template with implicit AND."""
        query = parse_query('"response {num:<200} ms" healthy')
        self.assertTrue(apply_query(query, "healthy response 100 ms"))
        self.assertFalse(apply_query(query, "degraded response 100 ms"))
        self.assertFalse(apply_query(query, "healthy response 300 ms"))

    # ── whitespace flexibility ──────────────────────────────────────────

    def test_template_extra_whitespace_in_text(self):
        """Template tolerates multiple spaces in evaluated text."""
        query = parse_query('"took {num:<50} ms"')
        self.assertTrue(apply_query(query, "took  12  ms"))

    def test_template_tab_whitespace(self):
        """Template matches tab characters as whitespace."""
        query = parse_query('"took {num:<50} ms"')
        self.assertTrue(apply_query(query, "took\t12\tms"))

    # ── edge cases ──────────────────────────────────────────────────────

    def test_template_no_surrounding_text(self):
        """Template with only a placeholder (no literal text)."""
        query = parse_query('"{num:>5}"')
        self.assertTrue(apply_query(query, "the value is 10"))
        self.assertFalse(apply_query(query, "the value is 3"))

    def test_template_text_not_found(self):
        """Template fails when the literal text is not present."""
        query = parse_query('"took {num:<50} ms"')
        self.assertFalse(apply_query(query, "completed in 12 seconds"))

    def test_template_multiple_occurrences_first_fails(self):
        """Template succeeds if any occurrence in text satisfies comparisons."""
        query = parse_query('"run {num:<10} ok"')
        # First match: "run 50 ok" → 50 < 10 ✗ ;  second: "run 3 ok" → 3 < 10 ✓
        self.assertTrue(apply_query(query, "run 50 ok then run 3 ok"))

    def test_template_all_occurrences_fail(self):
        """Template fails when no occurrence satisfies comparisons."""
        query = parse_query('"run {num:<10} ok"')
        self.assertFalse(apply_query(query, "run 50 ok then run 30 ok"))

    def test_template_special_chars_in_literal(self):
        """Special regex chars in literal parts are properly escaped."""
        query = parse_query('"status (code) {num:=200}"')
        self.assertTrue(apply_query(query, "status (code) 200"))
        self.assertFalse(apply_query(query, "status code 200"))

    def test_template_with_dots_in_literal(self):
        """Dots in literal parts are escaped (not regex wildcards)."""
        query = parse_query('"v2.0 took {num:<50} ms"')
        self.assertTrue(apply_query(query, "v2.0 took 30 ms"))
        self.assertFalse(apply_query(query, "v2X0 took 30 ms"))

    def test_template_list_filtering(self):
        """Template works with list filtering via apply_query."""
        query = parse_query('"took {num:<50} ms"')
        texts = [
            "took 10 ms",
            "took 99 ms",
            "took 30 ms",
            "unrelated text",
        ]
        result = apply_query(query, texts)
        self.assertEqual(result, ["took 10 ms", "took 30 ms"])

    def test_template_user_scenario(self):
        """Full user scenario: 'test N Success evaluated in M ms'."""
        query = parse_query('"test 1 Success evaluated in {num:<50} ms"')
        self.assertTrue(apply_query(query, "test 1 Success evaluated in 12 ms"))
        self.assertFalse(apply_query(query, "test 1 Success evaluated in 80 ms"))
        # Literal "test 1" must match — different test number fails
        self.assertFalse(apply_query(query, "test 2 Success evaluated in 12 ms"))

    def test_template_date_with_datetime(self):
        """Template with datetime value in placeholder."""
        query = parse_query('"logged at {date:>2024-01-01T00:00:00}"')
        self.assertTrue(apply_query(query, "logged at 2024-06-15T12:30:00"))
        self.assertFalse(apply_query(query, "logged at 2023-12-31T23:59:59"))

    def test_template_compile_path(self):
        """Template compile() path works correctly for list filtering."""
        query = parse_query('"score {num:>=90} points"')
        texts = ["score 95 points", "score 50 points", "score 90 points"]
        result = apply_query(query, texts)
        self.assertEqual(result, ["score 95 points", "score 90 points"])


class TemplateCandidateTests(unittest.TestCase):
    def test_overlapping_candidates_are_all_considered(self):
        query = parse_query('"{num:>0} took {num:<100}"')
        self.assertTrue(apply_query(query, "1 took 200 took 50"))

    def test_numbers_are_matched_whole(self):
        query = parse_query('"{num:<50} ms"')
        self.assertFalse(apply_query(query, "took 150 ms"))
        self.assertTrue(apply_query(query, "took 49.5 ms"))

    def test_hyphen_is_not_a_sign_inside_templates(self):
        query = parse_query('"{num:<0} C"')
        self.assertTrue(apply_query(query, "temp -5 C"))
        self.assertFalse(apply_query(query, "pages 3-5 C"))

    def test_placeholder_kind_is_case_insensitive(self):
        self.assertTrue(apply_query(parse_query('"{NUM:>3} x"'), "5 x"))


if __name__ == "__main__":
    unittest.main()
