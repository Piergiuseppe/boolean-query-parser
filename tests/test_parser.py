#!/usr/bin/env python3
"""
Unit tests for the boolean query parser module.

These tests cover basic operations (AND, OR, NOT), complex nested expressions,
regex matching, and edge cases like empty queries and syntax errors.
"""

import unittest

from boolean_query_parser import QueryError, apply_query, parse_query


class TestBooleanQueryParser(unittest.TestCase):
    """Test cases for the Boolean Query Parser functionality."""

    def test_simple_text_matching(self):
        """Test basic text matching without boolean operations."""
        # Simple text matching
        query = parse_query("python")
        self.assertTrue(apply_query(query, "I love python programming"))
        self.assertFalse(apply_query(query, "I love programming"))
        
        # Case sensitivity
        query = parse_query("Python")
        self.assertFalse(apply_query(query, "I love python programming"))
        
        # Multiple words as a single token
        query = parse_query("\"python programming\"")
        self.assertTrue(apply_query(query, "I love python programming"))
        self.assertFalse(apply_query(query, "I love python and programming"))

    def test_and_operation(self):
        """Test AND operation between two terms."""
        query = parse_query("python AND programming")
        
        # Both terms present
        self.assertTrue(apply_query(query, "python programming is fun"))
        
        # Only one term present
        self.assertFalse(apply_query(query, "python is fun"))
        self.assertFalse(apply_query(query, "programming is fun"))
        
        # Neither term present
        self.assertFalse(apply_query(query, "coding is fun"))

    def test_or_operation(self):
        """Test OR operation between two terms."""
        query = parse_query("python OR java")
        
        # Both terms present
        self.assertTrue(apply_query(query, "python and java are programming languages"))
        
        # Only one term present
        self.assertTrue(apply_query(query, "python is my favorite language"))
        self.assertTrue(apply_query(query, "java is widely used"))
        
        # Neither term present
        self.assertFalse(apply_query(query, "programming in C++"))

    def test_not_operation(self):
        """Test NOT operation on a term."""
        query = parse_query("programming AND NOT python")
        
        # Term present but excluded term absent
        self.assertTrue(apply_query(query, "programming in java"))
        
        # Both terms present
        self.assertFalse(apply_query(query, "programming in python"))
        
        # Neither term present
        self.assertFalse(apply_query(query, "coding in python"))
        self.assertFalse(apply_query(query, "learning a new language"))

    def test_parentheses_grouping(self):
        """Test expressions with parentheses for grouping."""
        # (A OR B) AND C
        query = parse_query("(python OR java) AND programming")
        
        self.assertTrue(apply_query(query, "python programming is fun"))
        self.assertTrue(apply_query(query, "java programming is widespread"))
        self.assertFalse(apply_query(query, "python is a snake"))
        self.assertFalse(apply_query(query, "programming in C++"))
        
        # A AND (B OR C)
        query = parse_query("programming AND (python OR java)")
        
        self.assertTrue(apply_query(query, "programming in python is fun"))
        self.assertTrue(apply_query(query, "programming in java is common"))
        self.assertFalse(apply_query(query, "programming in C++"))
        self.assertFalse(apply_query(query, "python is a snake"))

    def test_nested_parentheses(self):
        """Test complex expressions with nested parentheses."""
        # A AND (B OR (C AND D))
        query = parse_query("programming AND (python OR (java AND enterprise))")
        
        self.assertTrue(apply_query(query, "programming in python is fun"))
        self.assertTrue(apply_query(query, "programming in java enterprise applications"))
        self.assertFalse(apply_query(query, "programming in java at home"))
        self.assertFalse(apply_query(query, "python is a snake"))

    def test_complex_boolean_expressions(self):
        """Test complex boolean expressions combining AND, OR, NOT, and parentheses."""
        # (A OR B) AND NOT C
        query = parse_query("(python OR java) AND NOT javascript")
        
        self.assertTrue(apply_query(query, "I love python programming"))
        self.assertTrue(apply_query(query, "java is widely used"))
        self.assertFalse(apply_query(query, "Python, Java, and JavaScript are all popular"))
        self.assertFalse(apply_query(query, "JavaScript is for web"))
        
        # A AND (B OR NOT C)
        query = parse_query("programming AND (python OR NOT javascript)")
        
        self.assertTrue(apply_query(query, "programming in python"))
        self.assertTrue(apply_query(query, "programming in C++"))  # Matches because it has programming but not javascript
        self.assertFalse(apply_query(query, "programming in javascript"))
        self.assertFalse(apply_query(query, "learning python"))

    def test_regex_matching(self):
        """Test regex pattern matching."""
        # Simple regex
        query = parse_query("/py.*n/")
        
        self.assertTrue(apply_query(query, "I love python programming"))
        self.assertTrue(apply_query(query, "The python snake is interesting"))
        self.assertFalse(apply_query(query, "Ruby is also a good language"))
        
        # Email regex
        query = parse_query('/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/')
        
        self.assertTrue(apply_query(query, "Contact me at user@example.com"))
        self.assertFalse(apply_query(query, "No email here"))
        
        # Combining regex with boolean operations
        query = parse_query("/py.*n/ AND NOT /javascript/")
        
        self.assertTrue(apply_query(query, "python programming is fun"))
        self.assertFalse(apply_query(query, "python and javascript programming"))

    def test_list_filtering(self):
        """Test filtering a list of texts with a query."""
        query = parse_query("python AND NOT javascript")
        
        texts = [
            "python programming is fun",
            "javascript is for web development",
            "python and javascript together",
            "neither of these terms",
            "just python"
        ]
        
        expected = [
            "python programming is fun",
            "just python"
        ]
        
        self.assertEqual(apply_query(query, texts), expected)

    def test_empty_query(self):
        """Test behavior with empty queries."""
        with self.assertRaises(QueryError):
            parse_query("")
        
        with self.assertRaises(QueryError):
            parse_query("   ")

    def test_invalid_queries(self):
        """Test error handling for invalid query syntax."""
        # Missing closing parenthesis
        with self.assertRaises(QueryError):
            parse_query("(python AND java")
        
        # Missing term after AND
        with self.assertRaises(QueryError):
            parse_query("python AND")
        
        # Double operators
        with self.assertRaises(QueryError):
            parse_query("python AND AND java")
        
        # Invalid regex
        with self.assertRaises(QueryError):
            parse_query("/[unclosed regex/")

    def test_invalid_regex_patterns(self):
        """Test error handling for invalid regex patterns."""
        # This test assumes that RegexNode validates patterns during construction
        with self.assertRaises(QueryError):
            query = parse_query("/[invalid regex pattern(/")
            apply_query(query, "some text")

    def test_operator_precedence(self):
        """Test that operators follow the correct precedence."""
        # AND has higher precedence than OR
        # This should be interpreted as (A AND B) OR C, not A AND (B OR C)
        query = parse_query("python AND java OR javascript")
        
        # Would be false if interpreted as A AND (B OR C)
        self.assertTrue(apply_query(query, "javascript programming"))
        
        # NOT has higher precedence than AND
        # This should be interpreted as A AND (NOT B), not (A AND B) NOT
        query = parse_query("python AND NOT java")
        
        # Would be true if interpreted as (A AND B) NOT
        self.assertFalse(apply_query(query, "python java programming"))

    def test_edge_case_single_characters(self):
        """Test queries with single character terms."""
        query = parse_query("a AND b")
        
        self.assertTrue(apply_query(query, "a b"))
        self.assertFalse(apply_query(query, "a c"))
        self.assertFalse(apply_query(query, "c b"))
        self.assertFalse(apply_query(query, "c d"))


class TestRegexFeatures(unittest.TestCase):
    """Test cases specifically focusing on regex pattern matching capabilities."""

    def test_basic_regex_patterns(self):
        """Test basic regex pattern matching."""
        # Simple word pattern with case insensitive flag
        query = parse_query("/python/i")
        self.assertTrue(apply_query(query, "This is PYTHON language"))
        self.assertTrue(apply_query(query, "This is Python language"))
        
        # Without case insensitive flag
        query = parse_query("/python/")
        self.assertFalse(apply_query(query, "This is PYTHON language"))
        self.assertTrue(apply_query(query, "This is python language"))

    def test_regex_with_flags(self):
        """Test regex patterns with various flags."""
        # Multiline flag
        text = "First line\nSecond line with python\nThird line"
        query = parse_query("/^Second.*python$/m")
        self.assertTrue(apply_query(query, text))
        
        # Dot-all flag (s)
        text = "Start\nMiddle\nEnd"
        query = parse_query("/Start.*End/s")
        self.assertTrue(apply_query(query, text))
        
        query = parse_query("/Start.*End/")  # Without s flag
        self.assertFalse(apply_query(query, text))

    def test_complex_email_regex(self):
        """Test complex email validation regex."""
        email_regex = "/([A-Za-z0-9]+[._-])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\\.[A-Za-z]{2,})/"
        query = parse_query(email_regex)
        
        # Valid emails
        self.assertTrue(apply_query(query, "Contact us at info@example.com for more information"))
        self.assertTrue(apply_query(query, "My email is john.doe@example.co.uk"))
        self.assertTrue(apply_query(query, "Send to: jane_doe123@sub-domain.example.org"))
        
        # Invalid emails
        self.assertFalse(apply_query(query, "Invalid email: @example.com"))
        self.assertFalse(apply_query(query, "Invalid email: user@.com"))
        self.assertFalse(apply_query(query, "No email here"))

    def test_url_regex(self):
        """Test URL matching regex."""
        # Fixed URL regex pattern with proper escaping
        url_regex = "/(https?:\\/\\/)?([\\da-z\\.-]+)\\.([a-z\\.]{2,6})([\\/?&=#\\w \\.-]*)/i"
        query = parse_query(url_regex)
        
        # Valid URLs
        self.assertTrue(apply_query(query, "Visit https://www.example.com/path/to/resource"))
        self.assertTrue(apply_query(query, "Check out example.org for more info"))
        self.assertTrue(apply_query(query, "Domain: sub.domain.co.uk/page"))
        
        # Invalid or no URLs
        self.assertFalse(apply_query(query, "Just plain text"))
        self.assertFalse(apply_query(query, "Invalid: http://"))

    def test_phone_number_regex(self):
        """Test phone number pattern matching."""
        # US phone format: (123) 456-7890 or 123-456-7890
        phone_regex = "/\\(?\\d{3}\\)?[- ]?\\d{3}[- ]?\\d{4}/"
        query = parse_query(phone_regex)
        
        # Valid phone numbers
        self.assertTrue(apply_query(query, "Call (123) 456-7890 for support"))
        self.assertTrue(apply_query(query, "Phone: 123-456-7890"))
        self.assertTrue(apply_query(query, "Contact 1234567890"))
        
        # Invalid phone numbers
        self.assertFalse(apply_query(query, "Call 123-45-6789"))
        self.assertFalse(apply_query(query, "No phone number"))

    def test_regex_with_capturing_groups(self):
        """Test regex patterns with capturing groups."""
        # Match HTML tags
        tag_regex = "/\\<([a-z][a-z0-9]*)(\\s[^\\>]*)?\\>([^\\<]*)\\<\\/\\1\\>/i"
        query = parse_query(tag_regex)
        
        # Valid HTML
        self.assertTrue(apply_query(query, "<div>Content</div>"))
        self.assertTrue(apply_query(query, "<p class=\"text\">Paragraph</p>"))
        
        # Invalid HTML
        self.assertFalse(apply_query(query, "<div>Unclosed"))
        self.assertFalse(apply_query(query, "<div>Wrong closing</span>"))

    def test_regex_with_lookahead_lookbehind(self):
        """Test regex patterns with lookahead and lookbehind assertions."""
        # Password validation: at least 8 chars, one uppercase, one lowercase, one digit
        password_regex = "/^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{8,}$/"
        query = parse_query(password_regex)
        
        # Valid passwords
        self.assertTrue(apply_query(query, "Password123"))
        self.assertTrue(apply_query(query, "Complex1Password"))
        
        # Invalid passwords
        self.assertFalse(apply_query(query, "password")) # No uppercase, no digit
        self.assertFalse(apply_query(query, "PASSWORD123")) # No lowercase
        self.assertFalse(apply_query(query, "Pass1")) # Too short

    def test_combining_regex_with_boolean(self):
        """Test combining multiple regex patterns with boolean operators."""
        # Match text containing a date format AND an email - using simpler regex
        date_email_query = parse_query("/\\d{2}[-.]\\d{2}[-.]\\d{4}/ AND /\\w+@\\w+\\.\\w{2,}/")
        
        # Contains both date and email
        self.assertTrue(apply_query(date_email_query, "Date: 01.01.2023 - Contact: user@example.com"))
        
        # Missing one pattern
        self.assertFalse(apply_query(date_email_query, "Date: 01.01.2023 only"))
        self.assertFalse(apply_query(date_email_query, "Email: user@example.com only"))
        
        # Complex query with NOT
        complex_query = parse_query("/python/i AND NOT (/hello/ OR /world/)")
        
        self.assertTrue(apply_query(complex_query, "Python programming"))
        self.assertFalse(apply_query(complex_query, "Python hello programming"))
        self.assertFalse(apply_query(complex_query, "Python world"))

    def test_regex_escape_sequences(self):
        """Test regex patterns with escape sequences."""
        # Match literal period followed by digits
        period_query = parse_query("/\\.\\d+/")
        
        self.assertTrue(apply_query(period_query, "Price is .99"))
        self.assertTrue(apply_query(period_query, "Version 1.23"))
        self.assertFalse(apply_query(period_query, "No match here"))
        
        # Use a simpler path pattern without tricky escapes
        path_query = parse_query("/abc123/")
        
        self.assertTrue(apply_query(path_query, "This contains abc123 in it"))
        self.assertFalse(apply_query(path_query, "No match here"))


class TestImplicitAND(unittest.TestCase):
    """Test cases for implicit AND (adjacent terms without an explicit operator)."""

    def test_implicit_and_two_terms(self):
        """Test that two adjacent terms are implicitly ANDed."""
        query = parse_query("python java")
        self.assertTrue(apply_query(query, "python and java are popular"))
        self.assertFalse(apply_query(query, "python is great"))
        self.assertFalse(apply_query(query, "java is great"))

    def test_implicit_and_with_not(self):
        """Test implicit AND before NOT (e.g. 'error NOT warning')."""
        query = parse_query('error NOT "permission denied"')
        self.assertTrue(apply_query(query, "error: file not found"))
        self.assertFalse(apply_query(query, "error: permission denied"))
        self.assertFalse(apply_query(query, "success"))

    def test_implicit_and_three_terms(self):
        """Test implicit AND with three adjacent terms."""
        query = parse_query("python web framework")
        self.assertTrue(apply_query(query, "python web framework django"))
        self.assertFalse(apply_query(query, "python web"))
        self.assertFalse(apply_query(query, "web framework"))

    def test_implicit_and_mixed_with_explicit(self):
        """Test mixing implicit AND with explicit OR."""
        query = parse_query("python flask OR django")
        # This is: (python AND flask) OR django  (because AND > OR)
        self.assertTrue(apply_query(query, "python flask app"))
        self.assertTrue(apply_query(query, "django app"))
        self.assertFalse(apply_query(query, "python app"))

    def test_implicit_and_with_parentheses(self):
        """Test implicit AND with parenthesized sub-expression."""
        query = parse_query("python (flask OR django)")
        self.assertTrue(apply_query(query, "python flask app"))
        self.assertTrue(apply_query(query, "python django app"))
        self.assertFalse(apply_query(query, "python express app"))
        self.assertFalse(apply_query(query, "flask app"))

    def test_implicit_and_with_regex(self):
        """Test implicit AND between text and regex."""
        query = parse_query('python /\\d+/')
        self.assertTrue(apply_query(query, "python 3"))
        self.assertTrue(apply_query(query, "python version 3.12"))
        self.assertFalse(apply_query(query, "python is great"))
        self.assertFalse(apply_query(query, "version 3.12"))


class TestRegexForwardSlashBug(unittest.TestCase):
    """Test cases for regex patterns containing escaped forward slashes."""

    def test_regex_with_escaped_slash_and_flags(self):
        """Test regex with escaped forward slash AND flags (this worked before)."""
        query = parse_query('/a\\/b/i')
        self.assertTrue(apply_query(query, "This has A/B in it"))
        self.assertFalse(apply_query(query, "This has no match"))

    def test_regex_with_escaped_slash_no_flags(self):
        """Test regex with escaped forward slash but NO flags (was buggy before)."""
        query = parse_query('/a\\/b/')
        self.assertTrue(apply_query(query, "This has a/b in it"))
        self.assertFalse(apply_query(query, "This has no match"))

    def test_regex_url_pattern_no_flags(self):
        """Test a URL-like regex pattern with forward slashes and no flags."""
        query = parse_query('/https?:\\/\\//')
        self.assertTrue(apply_query(query, "Visit http://example.com"))
        self.assertTrue(apply_query(query, "Visit https://example.com"))
        self.assertFalse(apply_query(query, "No URL here"))


class TestReadmeExamples(unittest.TestCase):
    """Verify that all examples from the README actually work correctly."""

    def test_basic_example(self):
        """Test the Basic Example from README."""
        documents = [
            "The quick brown fox jumps over the lazy dog",
            "Python is a programming language",
            "The Python programming language is powerful and easy to learn",
            "Regular expressions can be complex but useful"
        ]

        query = 'Python AND programming AND NOT complex'
        parsed_query = parse_query(query)
        matching_documents = [doc for doc in documents if apply_query(parsed_query, doc)]

        self.assertEqual(matching_documents, [
            "Python is a programming language",
            "The Python programming language is powerful and easy to learn",
        ])

    def test_advanced_example(self):
        """Test the Advanced Example with Nested Expressions from README."""
        query = '(Python OR programming) AND (language OR easy) AND NOT (complex OR difficult)'
        parsed_query = parse_query(query)

        documents = [
            "Python is a great language for beginners",
            "Programming can be complex and difficult at times",
            "Python makes programming tasks easy to accomplish",
            "This text has nothing relevant"
        ]

        results = {doc: apply_query(parsed_query, doc) for doc in documents}

        self.assertTrue(results["Python is a great language for beginners"])
        self.assertFalse(results["Programming can be complex and difficult at times"])
        self.assertTrue(results["Python makes programming tasks easy to accomplish"])
        self.assertFalse(results["This text has nothing relevant"])

    def test_regex_example(self):
        """Test the Using Regular Expressions example from README."""
        query = '/py.*on/i AND NOT /difficult/'
        parsed_query = parse_query(query)

        documents = [
            "Python is easy to learn",
            "python programming is fun",
            "This is difficult Python code",
            "PyThOn is case-insensitive in this example"
        ]

        matching = [doc for doc in documents if apply_query(parsed_query, doc)]
        self.assertEqual(matching, [
            "Python is easy to learn",
            "python programming is fun",
            "PyThOn is case-insensitive in this example",
        ])

    def test_regex_flags_case_insensitive(self):
        """Test the case-insensitive regex flag example from README."""
        query = '/python/i'
        parsed_query = parse_query(query)
        self.assertTrue(apply_query(parsed_query, "This contains PYTHON"))

    def test_regex_flags_multiline(self):
        """Test the multiline regex flag example from README."""
        multiline_text = "First line\nSecond line with python\nThird line"
        query = '/^Second.*python$/m'
        parsed_query = parse_query(query)
        self.assertTrue(apply_query(parsed_query, multiline_text))

    def test_regex_flags_dotall(self):
        """Test the dot-all regex flag example from README."""
        text_with_newlines = "Start\nMiddle\nEnd"
        query = '/Start.*End/s'
        parsed_query = parse_query(query)
        self.assertTrue(apply_query(parsed_query, text_with_newlines))

    def test_complex_regex_email(self):
        """Test the email regex example from README."""
        email_pattern = '/([A-Za-z0-9]+[._-])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\\.[A-Za-z]{2,})/'
        email_query = parse_query(email_pattern)
        self.assertTrue(apply_query(email_query, "Contact us at info@example.com"))

    def test_complex_regex_html(self):
        """Test the HTML tag regex example from README."""
        html_pattern = '/\\<([a-z][a-z0-9]*)(\\s[^\\>]*)?\\>([^\\<]*)\\<\\/\\1\\>/i'
        html_query = parse_query(html_pattern)
        self.assertTrue(apply_query(html_query, "<div>Content</div>"))

    def test_complex_regex_password(self):
        """Test the password validation regex example from README."""
        password_pattern = '/^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{8,}$/'
        password_query = parse_query(password_pattern)
        self.assertTrue(apply_query(password_query, "Password123"))


class TestEdgeCases(unittest.TestCase):
    """Additional edge case tests."""

    def test_standalone_not(self):
        """Test NOT as the only operator (without AND/OR)."""
        query = parse_query("NOT python")
        self.assertTrue(apply_query(query, "I love java"))
        self.assertFalse(apply_query(query, "I love python"))

    def test_double_not(self):
        """Test double NOT (NOT NOT)."""
        query = parse_query("NOT NOT python")
        self.assertTrue(apply_query(query, "I love python"))
        self.assertFalse(apply_query(query, "I love java"))

    def test_deeply_nested_parentheses(self):
        """Test deeply nested parentheses."""
        query = parse_query("((((python))))")
        self.assertTrue(apply_query(query, "python is great"))
        self.assertFalse(apply_query(query, "java is great"))

    def test_multiple_or_operators(self):
        """Test chaining multiple OR operators."""
        query = parse_query("python OR java OR rust OR go")
        self.assertTrue(apply_query(query, "I use rust"))
        self.assertTrue(apply_query(query, "I use go"))
        self.assertFalse(apply_query(query, "I use C++"))

    def test_multiple_and_operators(self):
        """Test chaining multiple AND operators."""
        query = parse_query("python AND web AND framework AND fast")
        self.assertTrue(apply_query(query, "python web framework that is fast"))
        self.assertFalse(apply_query(query, "python web framework"))

    def test_quoted_string_with_single_quotes(self):
        """Test quoted strings with single quotes."""
        query = parse_query("'hello world'")
        self.assertTrue(apply_query(query, "say hello world please"))
        self.assertFalse(apply_query(query, "hello dear world"))

    def test_empty_quoted_string(self):
        """Test empty quoted string matches everything."""
        query = parse_query('""')
        self.assertTrue(apply_query(query, "anything"))
        self.assertTrue(apply_query(query, ""))

    def test_unrecognized_character_raises_error(self):
        """Test that unrecognized characters raise a clear error."""
        with self.assertRaises(QueryError):
            parse_query("python + java")

        with self.assertRaises(QueryError):
            parse_query("file.txt")

        with self.assertRaises(QueryError):
            parse_query("price $100")

    def test_list_filtering_empty_list(self):
        """Test filtering an empty list."""
        query = parse_query("python")
        self.assertEqual(apply_query(query, []), [])

    def test_list_filtering_no_matches(self):
        """Test filtering a list with no matches."""
        query = parse_query("python")
        texts = ["java is great", "rust is fast"]
        self.assertEqual(apply_query(query, texts), [])

    def test_unclosed_quoted_string(self):
        """Test unclosed quoted string is handled gracefully."""
        # An unclosed quote should still parse (takes until end of string)
        query = parse_query('"hello')
        self.assertTrue(apply_query(query, "say hello"))
        self.assertFalse(apply_query(query, "say goodbye"))

    def test_or_precedence_lower_than_and(self):
        """Test that OR has lower precedence than AND."""
        # a OR b AND c  should be  a OR (b AND c)
        query = parse_query("alpha OR beta AND gamma")
        self.assertTrue(apply_query(query, "alpha only"))        # alpha matches
        self.assertTrue(apply_query(query, "beta gamma here"))   # beta AND gamma
        self.assertFalse(apply_query(query, "beta only"))        # beta without gamma
        self.assertFalse(apply_query(query, "gamma only"))       # gamma without beta

    def test_complex_mixed_implicit_explicit(self):
        """Test complex query mixing implicit AND, explicit AND, OR, NOT."""
        query = parse_query('(python OR ruby) NOT "hello world" AND web')
        self.assertTrue(apply_query(query, "python web app"))
        self.assertTrue(apply_query(query, "ruby web framework"))
        self.assertFalse(apply_query(query, "python hello world web"))
        self.assertFalse(apply_query(query, "java web app"))


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
        """Ensure _compile() closure gives same results as evaluate()."""
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
            closure = q._compile()
            for t in texts:
                self.assertEqual(
                    q.evaluate(t),
                    closure(t),
                    msg=f"Mismatch for query={qs!r}, text={t!r}"
                )


if __name__ == "__main__":
    unittest.main()

