import pytest
from utils.recovery import RecoveryStrategy, RecoveryAnalyzer
from parser import Grammar, Rule, Token, Expression, Term


class MockToken:
    def __init__(self, type_name, value):
        self.type = type_name
        self.value = value


class TestRecoveryStrategy:
    def test_initialization(self):
        tokens = [MockToken("A", "a")]
        sync_tokens = {"Rule": {"B"}}
        strategy = RecoveryStrategy(tokens, sync_tokens, enable_recovery=True)
        assert strategy.tokens == tokens
        assert strategy.sync_tokens == sync_tokens
        assert strategy.enable_recovery is True
        assert strategy.errors == []

    def test_skip_to_sync_found(self):
        tokens = [MockToken("A", "a"), MockToken("B", "b"), MockToken("C", "c")]
        sync_tokens = {"Rule": {"C"}}
        strategy = RecoveryStrategy(tokens, sync_tokens, enable_recovery=True)

        # Start at 0, should skip A and B, stop at C (index 2)
        new_pos = strategy.skip_to_sync(0, "Rule")
        assert new_pos == 2
        assert tokens[new_pos].type == "C"

    def test_skip_to_sync_not_found(self):
        tokens = [MockToken("A", "a"), MockToken("B", "b")]
        sync_tokens = {"Rule": {"C"}}
        strategy = RecoveryStrategy(tokens, sync_tokens, enable_recovery=True)

        # Should go to end of tokens
        new_pos = strategy.skip_to_sync(0, "Rule")
        assert new_pos == 2  # len(tokens)

    def test_skip_to_sync_disabled(self):
        tokens = [MockToken("A", "a")]
        sync_tokens = {"Rule": {"A"}}
        strategy = RecoveryStrategy(tokens, sync_tokens, enable_recovery=False)

        # Should not move
        new_pos = strategy.skip_to_sync(0, "Rule")
        assert new_pos == 0

    def test_skip_to_sync_no_sync_set(self):
        tokens = [MockToken("A", "a")]
        sync_tokens = {}
        strategy = RecoveryStrategy(tokens, sync_tokens, enable_recovery=True)

        # Should not move
        new_pos = strategy.skip_to_sync(0, "Rule")
        assert new_pos == 0

    def test_record_error(self):
        tokens = [MockToken("A", "a")]
        strategy = RecoveryStrategy(tokens, {}, enable_recovery=True)

        strategy.record_error("Error msg", 0, ["B"])
        errors = strategy.get_errors()
        assert len(errors) == 1
        assert errors[0]["message"] == "Error msg"
        assert errors[0]["position"] == 0
        assert errors[0]["expected"] == ["B"]
        assert errors[0]["token"] == tokens[0]

    def test_record_error_eof(self):
        tokens = []
        strategy = RecoveryStrategy(tokens, {}, enable_recovery=True)

        strategy.record_error("Error msg", 0, ["B"])
        errors = strategy.get_errors()
        assert errors[0]["token"] is None


class TestRecoveryAnalyzerCoverage:
    def test_analyze_empty_grammar(self):
        grammar = Grammar("Empty", [], [])
        analyzer = RecoveryAnalyzer(grammar)
        sync = analyzer.analyze()
        assert sync == {}

    def test_analyze_literals(self):
        # Rule: | 'lit' -> pass
        tokens = []
        expr = Expression([Term("'lit'", "")], "pass")
        rule = Rule([expr], "Rule")
        grammar = Grammar("LitGrammar", tokens, [rule])

        analyzer = RecoveryAnalyzer(grammar)
        sync = analyzer.analyze()

        # FIRST(Rule) should contain 'lit'
        assert "lit" in analyzer.first_sets["Rule"]

    def test_analyze_follow_propagation(self):
        # Rule A: B C
        # Rule B: 'b'
        # Rule C: 'c'
        # FOLLOW(B) should include FIRST(C) -> 'c'

        tokens = []
        expr_b = Expression([Term("'b'", "")], "pass")
        rule_b = Rule([expr_b], "B")

        expr_c = Expression([Term("'c'", "")], "pass")
        rule_c = Rule([expr_c], "C")

        expr_a = Expression([Term("B", ""), Term("C", "")], "pass")
        rule_a = Rule([expr_a], "A", is_start=True)

        grammar = Grammar("FollowGrammar", tokens, [rule_a, rule_b, rule_c])

        analyzer = RecoveryAnalyzer(grammar)
        sync = analyzer.analyze()

        assert "c" in analyzer.follow_sets["B"]
        assert "c" in sync["B"]
