import unittest
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linter.venom_linter import VenomLinter


class TestLinter(unittest.TestCase):
    def test_valid_grammar(self):
        code = """
grammar Test:
    tokens:
        plus: \+
    end

    rule A:
        'a'
    end
end
"""
        linter = VenomLinter("test.apy", content=code)

        linter.lint()
        # Should have no errors
        errors = [d for d in linter.diagnostics if d["severity"] == "Error"]
        self.assertEqual(len(errors), 0, f"Found errors: {errors}")

    def test_invalid_grammar(self):
        code = """
grammar Test:
    rule A:
        # Missing body or invalid syntax
"""
        linter = VenomLinter("test.apy", content=code)
        linter.lint()
        # Should have errors
        errors = [d for d in linter.diagnostics if d["severity"] == "Error"]
        self.assertTrue(len(errors) > 0)


if __name__ == "__main__":
    unittest.main()
