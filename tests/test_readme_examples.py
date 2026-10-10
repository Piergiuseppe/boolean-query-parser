import unittest

from boolean_query_parser import apply_query, parse_query


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


if __name__ == "__main__":
    unittest.main()
