import unittest
import textwrap
from parser import Parser, Grammar, Token, Rule, TestCase


class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

    def test_simple_grammar(self):
        code = textwrap.dedent("""
        grammar TestGrammar:
            tokens:
                NUMBER: \d+
                PLUS: \+
            end

            start rule expr:
                | NUMBER -> Number
                | expr PLUS expr -> Add
            end
        end
        """)
        grammars = self.parser.parse(code)
        self.assertEqual(len(grammars), 1)
        grammar = grammars[0]
        self.assertEqual(grammar.name, "TestGrammar")
        self.assertEqual(len(grammar.tokens), 2)
        self.assertEqual(len(grammar.rules), 1)

        # Check line numbers
        # NUMBER is on line 4
        self.assertEqual(grammar.tokens[0].name, "NUMBER")
        self.assertEqual(grammar.tokens[0].line, 4)

        # PLUS is on line 5
        self.assertEqual(grammar.tokens[1].name, "PLUS")
        self.assertEqual(grammar.tokens[1].line, 5)

        # Rule expr is on line 8
        self.assertEqual(grammar.rules[0].name, "expr")
        self.assertEqual(grammar.rules[0].line, 7)

    def test_tests_parsing(self):
        code = textwrap.dedent("""
        grammar TestGrammar:
            tokens:
                NUMBER: \d+
            end

            start rule expr:
                | NUMBER -> Number
            end

            test expr:
                "123" => Success
                "abc" => Fail
            end
        end
        """)
        grammars = self.parser.parse(code)
        grammar = grammars[0]
        self.assertEqual(len(grammar.tests), 1)
        test_suite = grammar.tests[0]
        self.assertEqual(len(test_suite.cases), 2)

        # Check line numbers
        # "123" => Success is on line 12
        self.assertEqual(test_suite.cases[0].input_text, "123")
        self.assertEqual(test_suite.cases[0].line, 12)

        # "abc" => Fail is on line 13
        self.assertEqual(test_suite.cases[1].input_text, "abc")
        self.assertEqual(test_suite.cases[1].line, 13)


if __name__ == "__main__":
    unittest.main()
