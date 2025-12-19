import pytest
import textwrap
from parser import Parser
from utils.generators import CodeGenerator
from testing.runner import run_tests_in_memory


class TestCheckGuards:
    def setup_method(self):
        self.parser = Parser()

    def test_parse_check_guard(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                NUMBER: \d+
            end

            start rule expr:
                | n:NUMBER -> Number(n) check int(n) > 0 then print("positive") else then print("non-positive")
            end
        end
        """)
        grammars = self.parser.parse(code)
        assert len(grammars) == 1
        grammar = grammars[0]
        rule = grammar.rules[0]
        expr = rule.expressions[0]

        assert expr.check_guard is not None
        assert expr.check_guard.condition == "int(n) > 0"
        assert expr.check_guard.then_code == 'print("positive")'
        assert expr.check_guard.else_code == 'print("non-positive")'

    def test_parse_check_guard_no_else(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                NUMBER: \d+
            end

            start rule expr:
                | n:NUMBER -> Number(n) check int(n) > 0 then print("positive")
            end
        end
        """)
        grammars = self.parser.parse(code)
        expr = grammars[0].rules[0].expressions[0]

        assert expr.check_guard is not None
        assert expr.check_guard.condition == "int(n) > 0"
        assert expr.check_guard.then_code == 'print("positive")'
        assert expr.check_guard.else_code is None

    def test_execution_check_guard(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                NUMBER: \d+
            end

            start rule expr:
                | n:NUMBER -> int(n) check int(n.value) > 5 then res = 100 else then res = 0
            end
            
            test expr:
                "6" => Yields(100)
                "4" => Yields(0)
            end
        end
        """)
        grammars = self.parser.parse(code)
        grammar = grammars[0]
        generator = CodeGenerator(grammar)
        code = generator.generate()

        # Run tests
        success = run_tests_in_memory(grammar, code)
        assert success

    def test_execution_check_guard_no_else(self):
        code = textwrap.dedent(r"""
        grammar TestGrammar:
            tokens:
                NUMBER: \d+
            end

            start rule expr:
                | n:NUMBER -> int(n) check int(n.value) > 5 then res = 100
            end
            
            test expr:
                "6" => Yields(100)
                "4" => Yields(4)
            end
        end
        """)
        grammars = self.parser.parse(code)
        grammar = grammars[0]
        generator = CodeGenerator(grammar)
        code = generator.generate()

        success = run_tests_in_memory(grammar, code)
        assert success
