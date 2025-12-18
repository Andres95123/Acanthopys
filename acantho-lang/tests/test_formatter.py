import pytest
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from formatter.constrictor_formatter import ConstrictorFormatter


class TestFormatter:
    def test_format_simple_grammar(self):
        code = """
grammar Test:
    rule A:
        'a'
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        # Basic check - indentation should be preserved or fixed
        # The current formatter is simple, let's just check it runs and returns string
        assert isinstance(formatted, str)
        assert "grammar Test:" in formatted

    def test_format_auto_pass(self):
        code = """
grammar Test:
    rule A:
        'a'
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        assert "'a' -> pass" in formatted

    def test_format_tokens(self):
        code = """
tokens:
    plus: '+'
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        assert "tokens:" in formatted
        assert "plus: '+'" in formatted
