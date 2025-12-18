import pytest
from testing.runner import match_with_wildcard


class TestRunnerUtils:
    def test_match_with_wildcard(self):
        assert match_with_wildcard("Node(1, 2)", "Node(...)")
        assert match_with_wildcard("Add(Number(1), Number(2))", "Add(...)")
        assert not match_with_wildcard("Node(1)", "Other(...)")
        assert match_with_wildcard("Literal('(')", "Literal('(')")
