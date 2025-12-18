import sys
import os
import pytest

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linter.venom_linter import VenomLinter


def test_valid_grammar():
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
    assert len(errors) == 0, f"Found errors: {errors}"


def test_invalid_grammar():
    code = """
grammar Test:
    rule A:
        # Missing body or invalid syntax
"""
    linter = VenomLinter("test.apy", content=code)
    linter.lint()
    # Should have errors
    errors = [d for d in linter.diagnostics if d["severity"] == "Error"]
    assert len(errors) > 0
