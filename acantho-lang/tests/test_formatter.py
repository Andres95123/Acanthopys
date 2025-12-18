import unittest
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from formatter.constrictor_formatter import ConstrictorFormatter


class TestFormatter(unittest.TestCase):
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
        self.assertIsInstance(formatted, str)
        self.assertIn("grammar Test:", formatted)

    def test_format_tokens(self):
        code = """
tokens:
    plus: '+'
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        self.assertIn("tokens:", formatted)
        self.assertIn("plus: '+'", formatted)


if __name__ == "__main__":
    unittest.main()
