import unittest

from testing.runner import match_with_wildcard


class TestRunnerUtils(unittest.TestCase):
    def test_match_with_wildcard(self):
        self.assertTrue(match_with_wildcard("Node(1, 2)", "Node(...)"))
        self.assertTrue(match_with_wildcard("Add(Number(1), Number(2))", "Add(...)"))
        self.assertFalse(match_with_wildcard("Node(1)", "Other(...)"))
        self.assertTrue(match_with_wildcard("Literal('(')", "Literal('(')"))


if __name__ == "__main__":
    unittest.main()
