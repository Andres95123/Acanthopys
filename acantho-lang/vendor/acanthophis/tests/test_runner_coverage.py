import pytest
from unittest.mock import MagicMock, patch
from testing.runner import run_tests_in_memory, match_with_wildcard
from utils.logging import Logger


# Mocks for Grammar structure
class MockRule:
    def __init__(self, name, is_start=False):
        self.name = name
        self.is_start = is_start


class MockTestCase:
    def __init__(self, input_text, expectation, expected_value=None):
        self.input_text = input_text
        self.expectation = expectation
        self.expected_value = expected_value


class MockTestSuite:
    def __init__(self, name, target_rule, cases):
        self.name = name
        self.target_rule = target_rule
        self.cases = cases


class MockGrammar:
    def __init__(self, name, rules, tests):
        self.name = name
        self.rules = rules
        self.tests = tests


# Helper to generate valid python code for runner
def generate_mock_parser_code(
    lexer_tokens=None,
    parser_result=None,
    parser_error=None,
    missing_lexer=False,
    missing_parser=False,
    missing_parse_method=False,
):
    code = """
class ParseError(Exception):
    pass
"""
    if not missing_lexer:
        code += f"""
class Lexer:
    def __init__(self, text):
        self.tokens = {lexer_tokens or []}
"""
    if not missing_parser:
        code += """
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
"""
        if not missing_parse_method:
            if parser_error:
                code += f"""
    def parse_Start(self):
        raise ParseError("{parser_error}")
"""
            else:
                code += f"""
    def parse_Start(self):
        return {repr(parser_result)}
"""
    return code


class TestRunnerCoverage:
    def test_match_with_wildcard(self):
        assert match_with_wildcard("Node(1, 2)", "Node(..., 2)")
        assert match_with_wildcard("Node(1, 2)", "Node(1, ...)")
        assert match_with_wildcard("Node(1, 2)", "Node(..., ...)")
        assert not match_with_wildcard("Node(1, 2)", "Node(3, ...)")

    def test_syntax_error_in_code(self):
        grammar = MockGrammar("Test", [], [])
        code = "def broken_syntax("  # Missing closing paren/colon
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is False
        logger.error.assert_called()
        assert "Failed to compile generated parser code" in logger.error.call_args[0][0]

    def test_runtime_error_in_code(self):
        grammar = MockGrammar("Test", [], [])
        code = "raise ValueError('Boom')"
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is False
        logger.error.assert_called()
        assert "Failed to execute generated parser code" in logger.error.call_args[0][0]

    def test_missing_lexer_parser(self):
        grammar = MockGrammar("Test", [], [])
        code = "x = 1"  # Valid code, but no Lexer/Parser
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is False
        logger.error.assert_called_with(
            "Could not find Lexer or Parser class in generated code."
        )

    def test_multiple_start_rules(self):
        grammar = MockGrammar("Test", [MockRule("A", True), MockRule("B", True)], [])
        code = generate_mock_parser_code()
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is True
        logger.info.assert_called_with(
            "Multiple start rules defined for grammar 'Test'. Suites must specify target rule."
        )

    def test_no_rules_error(self):
        grammar = MockGrammar("Test", [], [])
        code = generate_mock_parser_code()
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is False
        logger.error.assert_called_with("No rules defined in grammar 'Test'.")

    def test_no_start_rule_warning(self):
        # Should pick first rule as default
        grammar = MockGrammar("Test", [MockRule("FirstRule")], [])
        code = generate_mock_parser_code()
        logger = MagicMock(spec=Logger)

        # No tests, so it should pass setup and return True (0 tests passed)
        result = run_tests_in_memory(grammar, code, logger)

        assert result is True
        logger.warn.assert_any_call(
            "No start rule defined for grammar 'Test'. Using first rule 'FirstRule' as default."
        )

    def test_suite_no_target_rule(self):
        # Multiple start rules -> no default start rule
        grammar = MockGrammar(
            "Test",
            [MockRule("A", True), MockRule("B", True)],
            [MockTestSuite("Suite1", None, [])],
        )
        code = generate_mock_parser_code()
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is False
        logger.error.assert_called_with("No rule available to test in suite 'Suite1'.")

    def test_parse_method_missing(self):
        grammar = MockGrammar(
            "Test",
            [MockRule("Start", True)],
            [MockTestSuite("Suite1", "Start", [MockTestCase("input", "Success")])],
        )
        code = generate_mock_parser_code(missing_parse_method=True)
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is False
        logger.error.assert_called_with("Rule 'parse_Start' not found in parser.")

    def test_expectation_success_pass(self):
        grammar = MockGrammar(
            "Test",
            [MockRule("Start", True)],
            [MockTestSuite("Suite1", "Start", [MockTestCase("input", "Success")])],
        )
        code = generate_mock_parser_code(parser_result="OK")
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is True
        logger.success.assert_called()

    def test_expectation_success_fail(self):
        grammar = MockGrammar(
            "Test",
            [MockRule("Start", True)],
            [MockTestSuite("Suite1", "Start", [MockTestCase("input", "Success")])],
        )
        code = generate_mock_parser_code(parser_error="Failed")
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is False
        logger.error.assert_called()

    def test_expectation_fail_pass(self):
        grammar = MockGrammar(
            "Test",
            [MockRule("Start", True)],
            [MockTestSuite("Suite1", "Start", [MockTestCase("input", "Fail")])],
        )
        code = generate_mock_parser_code(parser_result="OK")
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is False

    def test_expectation_fail_fail(self):
        grammar = MockGrammar(
            "Test",
            [MockRule("Start", True)],
            [MockTestSuite("Suite1", "Start", [MockTestCase("input", "Fail")])],
        )
        code = generate_mock_parser_code(parser_error="Failed")
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is True

    def test_expectation_yields_match(self):
        grammar = MockGrammar(
            "Test",
            [MockRule("Start", True)],
            [
                MockTestSuite(
                    "Suite1", "Start", [MockTestCase("input", "Yields", "'OK'")]
                )
            ],
        )
        code = generate_mock_parser_code(parser_result="OK")
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is True

    def test_expectation_yields_mismatch(self):
        grammar = MockGrammar(
            "Test",
            [MockRule("Start", True)],
            [
                MockTestSuite(
                    "Suite1", "Start", [MockTestCase("input", "Yields", "'Expected'")]
                )
            ],
        )
        code = generate_mock_parser_code(parser_result="Actual")
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is False

    def test_expectation_yields_wildcard_match(self):
        grammar = MockGrammar(
            "Test",
            [MockRule("Start", True)],
            [
                MockTestSuite(
                    "Suite1",
                    "Start",
                    [MockTestCase("input", "Yields", "'Node(..., 2)'")],
                )
            ],
        )
        code = generate_mock_parser_code(parser_result="Node(1, 2)")  # String repr
        # Need to adjust generate_mock_parser_code to return string "Node(1, 2)" not string "'Node(1, 2)'"
        # But repr("Node(1, 2)") is "'Node(1, 2)'".
        # Wait, runner does `result_repr = repr(result)`.
        # If result is string "Node(1, 2)", repr is "'Node(1, 2)'".
        # If result is object Node(1, 2), repr is "Node(1, 2)".
        # Let's assume result is a string for simplicity, but we need to match the repr.

        # If expected is "Node(..., 2)", then result repr should be "Node(1, 2)".
        # So result should be an object whose repr is "Node(1, 2)".
        # Or result is string "Node(1, 2)" and expected is "'Node(..., 2)'".

        # Let's use string result.
        # result = "Node(1, 2)" -> repr = "'Node(1, 2)'"
        # expected = "'Node(..., 2)'"
        pass  # Logic handled in test body below

    def test_expectation_yields_wildcard_match_logic(self):
        # Custom code to return an object with specific repr
        code = """
class ParseError(Exception): pass
class Lexer:
    def __init__(self, text): self.tokens = []
class Node:
    def __repr__(self): return "Node(1, 2)"
class Parser:
    def __init__(self, tokens): pass
    def parse_Start(self): return Node()
"""
        grammar = MockGrammar(
            "Test",
            [MockRule("Start", True)],
            [
                MockTestSuite(
                    "Suite1", "Start", [MockTestCase("input", "Yields", "Node(..., 2)")]
                )
            ],
        )
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is True

    def test_unexpected_exception(self):
        # Exception that is NOT ParseError
        code = """
class ParseError(Exception): pass
class Lexer:
    def __init__(self, text): self.tokens = []
class Parser:
    def __init__(self, tokens): pass
    def parse_Start(self): raise ValueError("Random Error")
"""
        grammar = MockGrammar(
            "Test",
            [MockRule("Start", True)],
            [MockTestSuite("Suite1", "Start", [MockTestCase("input", "Success")])],
        )
        logger = MagicMock(spec=Logger)

        result = run_tests_in_memory(grammar, code, logger)

        assert result is False
        # Should hint about tokens
        logger.hint.assert_any_call("Tokens parsed: []")
