import unittest

from boolean_query_parser import QueryError, apply_query, parse_query


class TestStressAndNasty(unittest.TestCase):
    """
    Stress tests and adversarial inputs.

    These tests are deliberately "nasty" — deep nesting, complex regex,
    long texts, tricky operator combinations — to ensure the parser is
    robust and to prevent regressions in future releases.
    """

    # ── Deep nesting ──────────────────────────────────────────────────

    def test_deeply_nested_boolean_10_levels(self):
        """10 levels of nested parentheses with mixed operators."""
        query = parse_query(
            "((((((((((alpha AND beta) OR gamma) AND NOT delta) OR epsilon)"
            " AND zeta) OR NOT eta) AND theta) OR iota) AND kappa) OR lambda)"
        )
        # All positive terms present, negative ones absent
        text = "alpha beta gamma epsilon zeta theta iota kappa lambda"
        self.assertTrue(apply_query(query, text))
        # Only lambda — outermost OR
        self.assertTrue(apply_query(query, "lambda alone"))
        # Nothing matches
        self.assertFalse(apply_query(query, "completely unrelated content"))

    def test_20_terms_implicit_and(self):
        """20 consecutive terms with implicit AND — all must be present."""
        terms = [f"t{i}" for i in range(20)]
        query_str = " ".join(terms)
        query = parse_query(query_str)
        full_text = " ".join(terms)
        self.assertTrue(apply_query(query, full_text))
        # Remove last term
        partial_text = " ".join(terms[:-1])
        self.assertFalse(apply_query(query, partial_text))

    def test_20_terms_chained_or(self):
        """20 terms chained with OR — any one match is enough."""
        terms = [f"term{i}" for i in range(20)]
        query_str = " OR ".join(terms)
        query = parse_query(query_str)
        # Only the last term present
        self.assertTrue(apply_query(query, "term19"))
        # None present
        self.assertFalse(apply_query(query, "nothing here"))

    def test_alternating_and_or_not_chain(self):
        """Long chain: a AND b OR c AND NOT d OR e AND f ..."""
        query = parse_query(
            "alpha AND beta OR gamma AND NOT delta OR epsilon AND zeta"
        )
        # Should parse as: ((alpha AND beta) OR ((gamma AND NOT delta)) OR (epsilon AND zeta))
        self.assertTrue(apply_query(query, "alpha beta"))           # first AND branch
        self.assertTrue(apply_query(query, "gamma only"))           # gamma AND NOT delta
        self.assertFalse(apply_query(query, "gamma delta"))         # NOT delta fails
        self.assertTrue(apply_query(query, "epsilon zeta"))         # last AND branch
        self.assertFalse(apply_query(query, "alpha only"))          # alpha without beta

    # ── NOT chains ────────────────────────────────────────────────────

    def test_triple_not(self):
        """NOT NOT NOT x = NOT x."""
        query = parse_query("NOT NOT NOT python")
        self.assertFalse(apply_query(query, "python here"))
        self.assertTrue(apply_query(query, "java here"))

    def test_quadruple_not(self):
        """NOT NOT NOT NOT x = x (even number of NOTs cancel out)."""
        query = parse_query("NOT NOT NOT NOT python")
        self.assertTrue(apply_query(query, "python here"))
        self.assertFalse(apply_query(query, "java here"))

    def test_five_nots(self):
        """5 NOTs (odd) = NOT x."""
        query = parse_query("NOT NOT NOT NOT NOT python")
        self.assertFalse(apply_query(query, "python here"))
        self.assertTrue(apply_query(query, "java here"))

    # ── Regex stress ──────────────────────────────────────────────────

    def test_complex_email_regex_with_boolean_exclusion(self):
        """Full email regex + boolean filtering of shady TLDs."""
        query = parse_query(
            '/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}/ '
            'AND NOT /\\.(xyz|top|buzz)\\b/'
        )
        texts = [
            "Contact support@example.com for help",
            "admin@sketchy.xyz is suspicious",
            "billing@company.co.uk is legit",
            "deals@promo.buzz is spam",
            "devops@internal.dev is internal",
            "no email here",
        ]
        result = apply_query(query, texts)
        self.assertIn("Contact support@example.com for help", result)
        self.assertIn("billing@company.co.uk is legit", result)
        self.assertIn("devops@internal.dev is internal", result)
        self.assertNotIn("admin@sketchy.xyz is suspicious", result)
        self.assertNotIn("deals@promo.buzz is spam", result)
        self.assertNotIn("no email here", result)

    def test_log_level_regex_with_date_and_healthcheck_filter(self):
        """Multiline-anchored regex for log levels + date + NOT healthcheck."""
        query = parse_query(
            '(/^\\[ERROR\\]/m OR /^\\[FATAL\\]/m) '
            'AND /\\d{4}-\\d{2}-\\d{2}/ '
            'AND NOT /healthcheck/i'
        )
        self.assertTrue(apply_query(
            query, "[ERROR] 2025-03-15 — DB timeout"))
        self.assertTrue(apply_query(
            query, "[FATAL] 2025-03-15 — OOM killed"))
        # Excluded: healthcheck
        self.assertFalse(apply_query(
            query, "[ERROR] 2025-03-15 — Healthcheck failed"))
        # Excluded: no date
        self.assertFalse(apply_query(
            query, "[ERROR] no date here"))
        # Excluded: INFO level
        self.assertFalse(apply_query(
            query, "[INFO] 2025-03-15 — server started"))

    def test_url_detection_with_exclusions(self):
        """Regex URL detection excluding localhost and placeholder domains."""
        query = parse_query(
            '((/https?:\\/\\//i OR /www\\./) '
            'AND (/\\.com/ OR /\\.org/ OR /\\.io/)) '
            'AND NOT (/localhost/ OR /127\\.0\\.0\\.1/ OR /example\\.com/)'
        )
        self.assertTrue(apply_query(query, "https://github.com/project"))
        self.assertTrue(apply_query(query, "www.startup.io site"))
        self.assertTrue(apply_query(query, "https://pypi.org/package"))
        self.assertFalse(apply_query(query, "http://localhost:3000"))
        self.assertFalse(apply_query(query, "http://127.0.0.1:8080"))
        self.assertFalse(apply_query(query, "http://docs.example.com"))
        self.assertFalse(apply_query(query, "plain text no url"))

    def test_password_strength_regex_chain(self):
        """Multiple regex ANDed to validate password complexity."""
        query = parse_query(
            '/^.{0,50}$/ AND (/[A-Z]/ AND /[a-z]/ AND /[0-9]/ AND /[!@#$%^&*]/)'
        )
        self.assertTrue(apply_query(query, "MyP@ssw0rd!"))
        self.assertTrue(apply_query(query, "C0mpl3x!Pass"))
        self.assertTrue(apply_query(query, "GoodP4$$word"))
        # Missing uppercase
        self.assertFalse(apply_query(query, "password123!"))
        # Missing lowercase
        self.assertFalse(apply_query(query, "ABC123!@#"))
        # Missing digit
        self.assertFalse(apply_query(query, "AbCdEf!@#"))
        # Missing special
        self.assertFalse(apply_query(query, "Password123"))
        # Too long (>50 chars)
        self.assertFalse(apply_query(
            query,
            "ThisIsAVeryLongPasswordThatExceedsFiftyCharacters!A1x"
        ))

    def test_regex_with_all_flags_combined(self):
        """Regex using i + m + s flags simultaneously."""
        query = parse_query("/^hello.*world$/ims")
        text_multiline = "HELLO\nbeautiful\nWORLD"
        self.assertTrue(apply_query(query, text_multiline))
        text_no_match = "greeting\nbeautiful\nearth"
        self.assertFalse(apply_query(query, text_no_match))

    def test_regex_with_escaped_slashes_in_pattern(self):
        """Regex containing escaped forward slashes (previous bug area)."""
        query = parse_query('/a\\/b\\/c/')
        self.assertTrue(apply_query(query, "path: a/b/c"))
        self.assertFalse(apply_query(query, "path: a/b/d"))

    def test_regex_with_pipe_inside(self):
        """Regex with | alternation (not to be confused with OR operator)."""
        query = parse_query('/(cat|dog|bird)/')
        self.assertTrue(apply_query(query, "I have a cat"))
        self.assertTrue(apply_query(query, "I have a dog"))
        self.assertTrue(apply_query(query, "I have a bird"))
        self.assertFalse(apply_query(query, "I have a fish"))

    def test_regex_quantifiers_stress(self):
        """Regex with various quantifiers: *, +, ?, {n,m}."""
        query = parse_query('/^a{3,5}b+c?d*$/')
        self.assertTrue(apply_query(query, "aaab"))
        self.assertTrue(apply_query(query, "aaaaabcd"))
        self.assertTrue(apply_query(query, "aaabbcdddd"))
        self.assertFalse(apply_query(query, "aab"))      # too few a's
        self.assertFalse(apply_query(query, "aaaaaab"))   # too many a's

    # ── Quoted strings & special text ─────────────────────────────────

    def test_quoted_phrase_with_boolean_and_regex(self):
        """Combine quoted phrases, text, regex, and all operators."""
        query = parse_query(
            '"stack overflow" OR ("runtime error" AND /line \\d+/)'
        )
        self.assertTrue(apply_query(
            query, "stack overflow detected in heap"))
        self.assertTrue(apply_query(
            query, "runtime error at line 42"))
        # Has "runtime error" but no line number
        self.assertFalse(apply_query(
            query, "runtime error: segfault"))
        # Has line number but not "runtime error"
        self.assertFalse(apply_query(
            query, "warning on line 42"))

    def test_quoted_string_containing_operator_keywords(self):
        """Quoted strings with AND/OR/NOT inside should be treated as text."""
        query = parse_query('"fish AND chips"')
        self.assertTrue(apply_query(query, "I ate fish AND chips"))
        self.assertFalse(apply_query(query, "I ate fish and chips"))

    def test_quoted_operator_keywords_as_text(self):
        """Standalone quoted "AND", "OR", "NOT" must be text, not operators."""
        query = parse_query('"AND" OR "OR" OR "NOT"')
        self.assertTrue(apply_query(query, "this AND that"))
        self.assertTrue(apply_query(query, "this OR that"))
        self.assertTrue(apply_query(query, "this NOT that"))
        self.assertFalse(apply_query(query, "this with that"))

    def test_quoted_and_between_terms(self):
        """'x "AND" y' should be implicit AND of three text nodes."""
        query = parse_query('python "AND" java')
        # All three must be present: "python", "AND", "java"
        self.assertTrue(apply_query(query, "python AND java"))
        self.assertFalse(apply_query(query, "python java"))  # missing "AND"
        self.assertFalse(apply_query(query, "python AND"))   # missing "java"

    def test_quoted_string_with_escaped_quote(self):
        """Quoted string with escaped quote character inside."""
        query = parse_query('"say \\"hello\\""')
        self.assertTrue(apply_query(query, 'say "hello"'))
        self.assertFalse(apply_query(query, 'say hello'))

    # ── Semver / release-notes style complex query ────────────────────

    def test_semver_changelog_filter(self):
        """Complex 4-level nested query for filtering release notes."""
        query = parse_query(
            '((((/\\d+\\.\\d+\\.\\d+/ AND NOT /0\\.0\\./) OR "release") '
            'AND (changelog OR update)) OR "breaking change")'
        )
        texts = [
            "v2.1.0 changelog — added implicit AND",
            "breaking change: new API",
            "Internal refactor, no changelog",
            "Version 0.0.1 update — initial release",
            "v3.5.2 changelog: parser fix",
            "Just a regular commit message",
        ]
        result = apply_query(query, texts)
        self.assertIn("v2.1.0 changelog — added implicit AND", result)
        self.assertIn("breaking change: new API", result)
        self.assertIn("v3.5.2 changelog: parser fix", result)
        # 0.0.1 excluded by NOT /0\.0\./, but rescued by OR "release"
        # AND "update" is present → matches
        self.assertIn("Version 0.0.1 update — initial release", result)
        self.assertNotIn("Internal refactor, no changelog", result)
        self.assertNotIn("Just a regular commit message", result)

    # ── List filtering at scale ───────────────────────────────────────

    def test_large_list_filtering(self):
        """Filter a list of 10,000 items to verify correctness at scale."""
        query = parse_query("target AND /\\d{4}/ AND NOT exclude")
        texts = []
        expected = []
        for i in range(10000):
            if i % 7 == 0:
                t = f"target item {i:04d} good"
                texts.append(t)
                expected.append(t)
            elif i % 7 == 1:
                texts.append(f"target item {i:04d} exclude this")
            elif i % 7 == 2:
                texts.append(f"item {i:04d} without the keyword")
            else:
                texts.append(f"irrelevant text number {i}")
        result = apply_query(query, texts)
        self.assertEqual(result, expected)

    def test_filter_returns_original_order(self):
        """Ensure filtered results preserve the original list order."""
        query = parse_query("match")
        texts = ["no", "match B", "no", "match A", "no", "match C"]
        result = apply_query(query, texts)
        self.assertEqual(result, ["match B", "match A", "match C"])

    # ── Long text evaluation ──────────────────────────────────────────

    def test_very_long_text(self):
        """Evaluate a query against a very long text (100KB+)."""
        # Build a ~100KB text with the needle buried in the middle
        padding = "lorem ipsum dolor sit amet " * 2000  # ~52KB
        text = padding + "NEEDLE_FOUND_HERE" + padding
        query = parse_query("NEEDLE_FOUND_HERE AND NOT SHOULD_NOT_EXIST")
        self.assertTrue(apply_query(query, text))
        self.assertFalse(apply_query(query, padding))

    def test_regex_on_very_long_text(self):
        """Regex search on a very long text."""
        padding = "abcdefghij " * 5000  # ~55KB
        text = padding + "secret_token_12345" + padding
        query = parse_query("/secret_token_\\d+/")
        self.assertTrue(apply_query(query, text))
        query_no = parse_query("/secret_token_\\d+/ AND /MISSING/")
        self.assertFalse(apply_query(query_no, text))

    # ── Operator precedence edge cases ────────────────────────────────

    def test_precedence_not_binds_tighter_than_and(self):
        """NOT binds tighter than AND: 'a AND NOT b' = 'a AND (NOT b)'."""
        query = parse_query("alpha AND NOT beta")
        self.assertTrue(apply_query(query, "alpha gamma"))
        self.assertFalse(apply_query(query, "alpha beta"))

    def test_precedence_and_binds_tighter_than_or(self):
        """AND binds tighter than OR: 'a OR b AND c' = 'a OR (b AND c)'."""
        query = parse_query("alpha OR beta AND gamma")
        self.assertTrue(apply_query(query, "alpha alone"))
        self.assertTrue(apply_query(query, "beta gamma together"))
        self.assertFalse(apply_query(query, "beta alone"))

    def test_precedence_complex_no_parens(self):
        """Complex expression without parens, relying on precedence."""
        # alpha OR bravo AND NOT charlie OR delta AND echo
        # = alpha OR (bravo AND (NOT charlie)) OR (delta AND echo)
        query = parse_query("alpha OR bravo AND NOT charlie OR delta AND echo")
        self.assertTrue(apply_query(query, "just alpha"))
        self.assertTrue(apply_query(query, "bravo only"))               # bravo present, charlie absent → True
        self.assertFalse(apply_query(query, "bravo charlie together"))  # bravo AND NOT charlie fails
        self.assertTrue(apply_query(query, "delta echo together"))
        self.assertFalse(apply_query(query, "delta only"))              # delta without echo
        self.assertFalse(apply_query(query, "nothing relevant"))

    # ── Error handling: adversarial inputs ─────────────────────────────

    def test_missing_operand_after_and(self):
        """AND with missing right operand should raise."""
        with self.assertRaises(QueryError):
            parse_query("python AND")

    def test_missing_operand_after_or(self):
        """OR with missing right operand should raise."""
        with self.assertRaises(QueryError):
            parse_query("python OR")

    def test_missing_operand_after_not(self):
        """NOT with nothing after it should raise."""
        with self.assertRaises(QueryError):
            parse_query("NOT")

    def test_double_operator_and_and(self):
        """Double AND should raise."""
        with self.assertRaises(QueryError):
            parse_query("a AND AND b")

    def test_double_operator_or_or(self):
        """Double OR should raise."""
        with self.assertRaises(QueryError):
            parse_query("a OR OR b")

    def test_unmatched_opening_paren(self):
        """Unmatched '(' should raise."""
        with self.assertRaises(QueryError):
            parse_query("(a AND b")

    def test_unmatched_closing_paren(self):
        """Stray ')' should raise."""
        with self.assertRaises(QueryError):
            parse_query("a AND b)")

    def test_empty_parentheses(self):
        """Empty '()' should raise."""
        with self.assertRaises(QueryError):
            parse_query("()")

    def test_only_operator(self):
        """Standalone operator keyword should raise."""
        with self.assertRaises(QueryError):
            parse_query("AND")
        with self.assertRaises(QueryError):
            parse_query("OR")

    def test_special_characters_raise(self):
        """Special characters outside quotes/regex should raise."""
        for char in ['@', '#', '$', '%', '^', '&', '*', '+', '=', '~', '`']:
            with self.assertRaises(QueryError, msg=f"char '{char}' should raise"):
                parse_query(f"test {char} value")

    def test_unclosed_regex_raises(self):
        """Unclosed /regex should raise, not loop forever."""
        with self.assertRaises(QueryError):
            parse_query("/unclosed")

    def test_empty_regex_raises(self):
        """Empty regex // and //i should raise."""
        with self.assertRaises(QueryError):
            parse_query("//")
        with self.assertRaises(QueryError):
            parse_query("//i")
        with self.assertRaises(QueryError):
            parse_query("//ims")

    def test_invalid_regex_pattern(self):
        """Syntactically invalid regex should raise with clear message."""
        with self.assertRaises(QueryError):
            parse_query("/[invalid(/")

    def test_text_data_type_validation(self):
        """Passing wrong type to apply_query should raise TypeError."""
        query = parse_query("test")
        with self.assertRaises(TypeError):
            apply_query(query, 42)
        with self.assertRaises(TypeError):
            apply_query(query, {"key": "value"})

    # ── Implicit AND comprehensive ────────────────────────────────────

    def test_implicit_and_between_two_regexes(self):
        """Two adjacent regex literals are implicitly ANDed."""
        query = parse_query('/\\d+/ /[A-Z]+/')
        self.assertTrue(apply_query(query, "123 ABC"))
        self.assertFalse(apply_query(query, "123 abc"))
        self.assertFalse(apply_query(query, "no digits ABC"))

    def test_implicit_and_regex_then_text(self):
        """Regex followed by text — implicit AND."""
        query = parse_query('/error/i critical')
        self.assertTrue(apply_query(query, "ERROR: critical failure"))
        self.assertFalse(apply_query(query, "ERROR: minor issue"))
        self.assertFalse(apply_query(query, "INFO: critical notice"))

    def test_implicit_and_text_then_paren_group(self):
        """Text followed by parenthesized group — implicit AND."""
        query = parse_query('server (down OR unreachable)')
        self.assertTrue(apply_query(query, "server is down"))
        self.assertTrue(apply_query(query, "server unreachable"))
        self.assertFalse(apply_query(query, "server running fine"))
        self.assertFalse(apply_query(query, "database down"))

    def test_implicit_and_complex_mixed(self):
        """Complex mixing of implicit AND with explicit operators."""
        # python flask NOT ruby OR django → ((python AND flask AND NOT ruby) OR django)
        query = parse_query("python flask NOT ruby OR django")
        self.assertTrue(apply_query(query, "python flask app"))
        self.assertFalse(apply_query(query, "python flask ruby app"))
        self.assertTrue(apply_query(query, "django app"))
        self.assertFalse(apply_query(query, "python only"))

    # ── Compile / closure path ────────────────────────────────────────

    def test_compile_closure_matches_evaluate(self):
        """Ensure compile() closure gives same results as evaluate()."""
        queries = [
            "python AND (django OR flask)",
            "NOT NOT python",
            '/\\d+/ AND NOT /error/i',
            "(a OR b) AND (c OR d) AND NOT e",
            '"exact phrase" OR /regex/',
        ]
        texts = [
            "python django app with 42 items",
            "python flask and error log",
            "a c matched here",
            "exact phrase found",
            "regex pattern inside",
            "nothing matches at all",
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


if __name__ == "__main__":
    unittest.main()
