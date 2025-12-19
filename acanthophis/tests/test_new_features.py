import pytest
import textwrap
from parser.core import Parser
from utils.generators import CodeGenerator
from testing.runner import run_tests_in_memory
from utils.logging import Logger


def test_check_guard_multiline():
    grammar_text = textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end

        rule Test:
            | x:ID -> x
              check
                len(x) > 0
              then
                pass
        end
        
        test Test:
            "a" => Success
        end
    end
    """)
    parser = Parser()
    grammars = parser.parse(grammar_text)
    assert len(grammars) == 1
    grammar = grammars[0]

    rule = grammar.rules[0]
    expr = rule.expressions[0]
    assert expr.check_guard is not None
    assert "len(x) > 0" in expr.check_guard.condition

    generator = CodeGenerator(grammar)
    code = generator.generate()

    logger = Logger(verbose=False)
    success = run_tests_in_memory(grammar, code, logger)
    assert success


def test_error_function():
    grammar_text = textwrap.dedent("""
    grammar TestError:
        tokens:
            ID: [a-z]+
        end

        rule Test:
            | x:ID -> x
              check len(x) > 5
              then pass
              else then error("Too short")
        end
        
        test Test:
            "abcdef" => Success
            "abc" => Fail
        end
    end
    """)
    parser = Parser()
    grammars = parser.parse(grammar_text)
    grammar = grammars[0]

    generator = CodeGenerator(grammar, enable_recovery=True)
    code = generator.generate()

    logger = Logger(verbose=False)
    success = run_tests_in_memory(grammar, code, logger)
    assert success


def test_flexible_quotes():
    grammar_text = textwrap.dedent("""
    grammar TestQuotes:
        tokens:
            ID: [a-z]+
        end

        rule Test:
            | "foo" -> "double"
            | 'bar' -> 'single'
        end
        
        test Test:
            "foo" => Yields('double')
            "bar" => Yields('single')
        end
    end
    """)
    parser = Parser()
    grammars = parser.parse(grammar_text)
    grammar = grammars[0]

    generator = CodeGenerator(grammar)
    code = generator.generate()

    logger = Logger(verbose=False)
    success = run_tests_in_memory(grammar, code, logger)
    assert success


def test_flexible_quotes_in_error():
    grammar_text = textwrap.dedent("""
    grammar TestQuotesError:
        tokens:
            ID: [a-z]+
        end

        rule Test:
            | x:ID -> x
              check len(x) > 5
              then pass
              else then error('Too short')
        end
        
        test Test:
            "abc" => Fail
        end
    end
    """)
    parser = Parser()
    grammars = parser.parse(grammar_text)
    grammar = grammars[0]

    generator = CodeGenerator(grammar, enable_recovery=True)
    code = generator.generate()

    logger = Logger(verbose=False)
    success = run_tests_in_memory(grammar, code, logger)
    assert success
