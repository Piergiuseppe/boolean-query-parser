import unittest

from boolean_query_parser import QueryError, apply_query, parse_query


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


class RegexFlagTests(unittest.TestCase):
    def test_escaped_slash_followed_by_flags_keeps_the_pattern(self):
        query = parse_query("/a\\/i/i")
        self.assertTrue(apply_query(query, "A/I"))
        self.assertFalse(apply_query(query, "a"))

    def test_escaped_slash_before_closing_is_part_of_the_pattern(self):
        query = parse_query("/a\\/i/")
        self.assertTrue(apply_query(query, "a/i"))
        self.assertFalse(apply_query(query, "A/I"))

    def test_unsupported_flags_are_rejected(self):
        for query in ("/foo/g", "/foo/bar", "/foo/iu"):
            with self.subTest(query=query):
                with self.assertRaises(QueryError):
                    parse_query(query)

    def test_all_supported_flags_combine(self):
        query = parse_query("/^a.b # comment/imsx")
        self.assertTrue(apply_query(query, "x\nA\nB"))


if __name__ == "__main__":
    unittest.main()
