import pytest
import textwrap
from parser import Parser


class TestParser:
    def setup_method(self):
        self.parser = Parser()

    def test_simple_grammar(self):
        code = textwrap.dedent(r"""
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
        assert len(grammars) == 1
        grammar = grammars[0]
        assert grammar.name == "TestGrammar"
        assert len(grammar.tokens) == 2
        assert len(grammar.rules) == 1

        # Check line numbers
        # NUMBER is on line 4
        assert grammar.tokens[0].name == "NUMBER"
        assert grammar.tokens[0].line == 4

        # PLUS is on line 5
        assert grammar.tokens[1].name == "PLUS"
        assert grammar.tokens[1].line == 5

        # Rule expr is on line 8
        assert grammar.rules[0].name == "expr"
        assert grammar.rules[0].line == 7

    def test_tests_parsing(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                NUMBER: \d+
            end

            rule expr:
                NUMBER
            end

            test expr:
                "123" => Yields(match)
            end
        end
        """)
        grammars = self.parser.parse(code)
        assert len(grammars[0].tests) == 1
        test_suite = grammars[0].tests[0]
        assert test_suite.name == "expr"
        assert len(test_suite.cases) == 1
        assert test_suite.cases[0].input_text == "123"
        assert test_suite.cases[0].expectation == "Yields"
        assert test_suite.cases[0].expected_value == "match"

    def test_no_tokens_block(self):
        code = textwrap.dedent("""
        grammar TestGrammar:
            rule expr:
                | NUMBER -> Number
            end
        end
        """)
        with pytest.raises(Exception, match="No tokens detected"):
            self.parser.parse(code)

    def test_multiple_start_rules(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                NUMBER: \d+
            end

            start rule expr1:
                | NUMBER -> Number
            end

            start rule expr2:
                | NUMBER -> Number
            end
        end
        """)
        with pytest.raises(Exception, match="Multiple start rules defined"):
            self.parser.parse(code)

    def test_undefined_reference(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                NUMBER: \d+
            end

            rule expr:
                | UNDEFINED -> Number
            end
        end
        """)
        with pytest.raises(Exception, match="Undefined token or rule 'UNDEFINED'"):
            self.parser.parse(code)

    def test_no_grammar_found(self):
        code = "# Just comments"
        grammars = self.parser.parse(code)
        assert len(grammars) == 0

    def test_literal_in_rule(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                A: a
            end
            rule expr:
                | 'literal' -> Node
            end
        end
        """)
        grammars = self.parser.parse(code)
        assert len(grammars) == 1

    def test_test_suite_no_cases(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                A: a
            end
            rule expr:
                A
            end
            test expr:
                # Just a comment
                Invalid Line Here
            end
        end
        """)
        with pytest.raises(Exception, match="Invalid test syntax or no tests found"):
            self.parser.parse(code)

    def test_invalid_test_input_string(self):
        # Try to trigger ast.literal_eval error with invalid escape sequence
        # Note: The regex captures content inside quotes.
        # If we use a raw string in the test code, it will be passed to parser.
        # We want the parser to see a string containing \xZZ which is invalid in python string literal.
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                A: a
            end
            rule expr:
                A
            end
            test expr:
                "\xZZ" => Success
            end
        end
        """)
        with pytest.raises(Exception, match="Failed to parse test input string"):
            self.parser.parse(code)

    def test_invalid_yields_syntax(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                A: a
            end
            rule expr:
                A
            end
            test expr:
                "input" => Yields
            end
        end
        """)
        with pytest.raises(Exception, match="Invalid Yields syntax"):
            self.parser.parse(code)

    def test_empty_yields(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                A: a
            end
            rule expr:
                A
            end
            test expr:
                "input" => Yields()
            end
        end
        """)
        with pytest.raises(Exception, match=r"Yields\(\) is empty"):
            self.parser.parse(code)

    def test_invalid_expectation(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                A: a
            end
            rule expr:
                A
            end
            test expr:
                "input" => Unknown
            end
        end
        """)
        with pytest.raises(Exception, match="Invalid test expectation"):
            self.parser.parse(code)

    def test_no_start_rule_but_rules_exist(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                A: a
            end
            rule expr:
                A
            end
        end
        """)
        grammars = self.parser.parse(code)
        assert len(grammars) == 1
