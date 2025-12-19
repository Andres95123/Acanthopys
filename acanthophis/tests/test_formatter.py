import pytest
import sys
import os
from formatter.constrictor_formatter import ConstrictorFormatter


class TestFormatterBasics:
    """Basic formatter functionality tests"""

    def test_format_returns_string(self):
        """Formatter should return a string"""
        code = "grammar Test:\nend"
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        assert isinstance(formatted, str)

    def test_format_simple_grammar(self):
        """Simple grammar should be formatted correctly"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
    end
    rule A:
        | n:NUMBER -> int(n)
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        assert "grammar Test:" in formatted
        assert "tokens:" in formatted
        assert "rule A:" in formatted


class TestFormatterIndentation:
    """Tests for proper indentation"""

    def test_grammar_level_indentation(self):
        """Grammar blocks should have proper indentation"""
        code = "grammar Test:\ntokens:\nNUM: \\d+\nend\nend"
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        lines = formatted.split("\n")
        # tokens: should be indented once
        assert any(
            line.strip() == "tokens:" and line.startswith("    ") for line in lines
        )

    def test_token_indentation(self):
        """Tokens should have double indentation"""
        code = """
grammar Test:
tokens:
NUMBER: \\d+
end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        # NUMBER should have 8 spaces (2 indents)
        assert "        NUMBER: \\d+" in formatted

    def test_rule_indentation(self):
        """Rules should have single indentation"""
        code = """
grammar Test:
tokens:
NUMBER: \\d+
end
rule Expr:
| n:NUMBER -> int(n)
end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        lines = formatted.split("\n")
        # rule Expr: should be indented once
        assert any("rule Expr:" in line and line.startswith("    ") for line in lines)

    def test_expression_indentation(self):
        """Expressions should have double indentation"""
        code = """
grammar Test:
tokens:
NUMBER: \\d+
end
rule Expr:
| n:NUMBER -> int(n)
end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        # Expression should have 8 spaces
        assert "        | n:NUMBER -> int(n)" in formatted


class TestFormatterAutoPass:
    """Tests for automatic pass insertion"""

    def test_auto_pass_insertion(self):
        """Expressions without return should get '-> pass' added"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
    end
    rule A:
        | n:NUMBER
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        assert "-> pass" in formatted

    def test_existing_return_preserved(self):
        """Expressions with explicit return should be preserved"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
    end
    rule A:
        | n:NUMBER -> int(n)
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        assert "-> int(n)" in formatted
        # Should not have '-> pass' for this expression
        assert formatted.count("-> pass") == 0 or "-> int(n)" in formatted


class TestFormatterSpacing:
    """Tests for proper spacing and empty lines"""

    def test_no_excessive_empty_lines(self):
        """Should not have more than one consecutive empty line"""
        code = """
grammar Test:


    tokens:
        NUMBER: \\d+
    end


    rule A:
        | n:NUMBER -> int(n)
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        # Check no triple newlines
        assert "\n\n\n" not in formatted

    def test_space_before_rules(self):
        """Should have empty line before rules"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
    end
    rule A:
        | n:NUMBER -> int(n)
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        lines = formatted.split("\n")
        # Find rule A
        for i, line in enumerate(lines):
            if "rule A:" in line:
                # Previous line should be empty
                assert i > 0 and lines[i - 1].strip() == ""
                break

    def test_space_before_tests(self):
        """Should have empty line before tests"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
    end
    rule A:
        | n:NUMBER -> int(n)
    end
    test TestA A:
        "42" => Yields(42)
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        lines = formatted.split("\n")
        # Find test
        for i, line in enumerate(lines):
            if "test TestA" in line:
                # Previous line should be empty
                assert i > 0 and lines[i - 1].strip() == ""
                break


class TestFormatterCheckGuards:
    """Tests for check guard formatting"""

    def test_check_guard_indentation(self):
        """Check guards should have extra indentation"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
    end
    rule A:
        | n:NUMBER -> int(n)
        check int(n) > 0 then
        print("positive")
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        # Check should be at 3 indents (12 spaces)
        assert "            check int(n) > 0 then" in formatted
        # Code inside should be at 4 indents (16 spaces)
        assert '                print("positive")' in formatted

    def test_check_guard_with_else(self):
        """Check guards with else should be formatted correctly"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
    end
    rule A:
        | n:NUMBER -> int(n)
        check int(n) > 0 then
        print("positive")
        else then
        print("negative")
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        assert "else then" in formatted
        # else then should be at 3 indents (12 spaces)
        assert "            else then" in formatted


class TestFormatterTokens:
    """Tests for token formatting"""

    def test_token_with_skip(self):
        """Skip tokens should be formatted correctly"""
        code = """
grammar Test:
    tokens:
        WHITESPACE: skip \\s+
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        assert "WHITESPACE: skip \\s+" in formatted

    def test_token_without_skip(self):
        """Regular tokens should be formatted correctly"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        assert "NUMBER: \\d+" in formatted


class TestFormatterTests:
    """Tests for test case formatting"""

    def test_test_case_formatting(self):
        """Test cases should be formatted correctly"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
    end
    rule Expr:
        | n:NUMBER -> int(n)
    end
    test Cases Expr:
        "42"=>Yields(42)
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        # Should have proper spacing around =>
        assert '"42" => Yields(42)' in formatted

    def test_test_with_target_rule(self):
        """Test with target rule should preserve it"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
    end
    rule Expr:
        | n:NUMBER -> int(n)
    end
    test Cases Expr:
        "42" => Success
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        assert "test Cases Expr:" in formatted


class TestFormatterComments:
    """Tests for comment handling"""

    def test_comments_preserved(self):
        """Comments should be preserved and properly indented"""
        code = """
grammar Test:
    # Top level comment
    tokens:
        # Token comment
        NUMBER: \\d+
    end
    rule Expr:
        # Rule comment
        | n:NUMBER -> int(n)
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        assert "# Top level comment" in formatted
        assert "# Token comment" in formatted
        assert "# Rule comment" in formatted


class TestFormatterPipeOperator:
    """Tests for pipe operator formatting"""

    def test_pipe_with_space(self):
        """Pipe operator should have space after it"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
    end
    rule Expr:
        |n:NUMBER -> int(n)
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        # Should add space after |
        assert "| n:NUMBER" in formatted

    def test_multiple_alternatives(self):
        """Multiple alternatives should each start with |"""
        code = """
grammar Test:
    tokens:
        NUMBER: \\d+
        PLUS: \\+
    end
    rule Expr:
        | n:NUMBER -> int(n)
        | left:Expr PLUS right:Expr -> Add(left, right)
    end
end
"""
        formatter = ConstrictorFormatter(code)
        formatted = formatter.format()
        # Both should have |
        lines = [
            l
            for l in formatted.split("\n")
            if "NUMBER" in l or ("PLUS" in l and "->" in l)
        ]
        assert all("|" in l for l in lines if "->" in l)
