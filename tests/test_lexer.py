import unittest

from boolean_query_parser import QuerySyntaxError
from boolean_query_parser.syntax import ComparisonLiteral, Lexer, RegexLiteral, TokenType


def kinds(query):
    return [token.type for token in Lexer(query).tokenize()]


class LexerTests(unittest.TestCase):
    def test_tokens_carry_position_and_source(self):
        tokens = Lexer('error AND "a \\"b\\"" /x\\/y/i num:>=3').tokenize()
        self.assertEqual(
            [(token.type, token.position, token.source) for token in tokens],
            [
                (TokenType.TEXT, 0, "error"),
                (TokenType.AND, 6, "AND"),
                (TokenType.TEXT, 10, '"a \\"b\\""'),
                (TokenType.REGEX, 20, "/x\\/y/i"),
                (TokenType.COMPARISON, 28, "num:>=3"),
                (TokenType.EOF, 35, ""),
            ],
        )

    def test_quoted_text_unescapes(self):
        token = Lexer('"say \\"hi\\""').tokenize()[0]
        self.assertEqual(token.value, 'say "hi"')

    def test_regex_keeps_escapes_and_splits_flags(self):
        token = Lexer("/a\\/i/im").tokenize()[0]
        self.assertEqual(token.value, RegexLiteral("a\\/i", "im"))

    def test_comparison_is_split_into_parts(self):
        token = Lexer('date:<="2024-01-01 10:00"').tokenize()[0]
        self.assertEqual(token.value, ComparisonLiteral("date", "<=", "2024-01-01 10:00"))

    def test_keywords_are_case_insensitive_unless_quoted(self):
        self.assertEqual(
            kinds('a and b or not c "AND"'),
            [
                TokenType.TEXT, TokenType.AND, TokenType.TEXT, TokenType.OR,
                TokenType.NOT, TokenType.TEXT, TokenType.TEXT, TokenType.EOF,
            ],
        )

    def test_bare_words_accept_inner_punctuation(self):
        tokens = Lexer("node.js C++ C# e-mail user@host snake_case").tokenize()
        self.assertEqual(
            [token.value for token in tokens[:-1]],
            ["node.js", "C++", "C#", "e-mail", "user@host", "snake_case"],
        )

    def test_quoted_placeholder_becomes_template(self):
        self.assertEqual(kinds('"took {num:<5} ms"')[0], TokenType.TEMPLATE)
        self.assertEqual(kinds('"took {foo:<5} ms"')[0], TokenType.TEXT)

    def test_tokenize_is_repeatable(self):
        lexer = Lexer("a b")
        self.assertEqual(lexer.tokenize(), lexer.tokenize())

    def test_errors_report_their_position(self):
        cases = {
            '"open': 0,
            "a 'open": 2,
            "a /open": 2,
            "a //": 2,
            "a + b": 2,
        }
        for query, position in cases.items():
            with self.subTest(query=query):
                with self.assertRaises(QuerySyntaxError) as caught:
                    Lexer(query).tokenize()
                self.assertEqual(caught.exception.position, position)


if __name__ == "__main__":
    unittest.main()
