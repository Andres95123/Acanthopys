"""
Error recovery module for Acanthopys Parser Generator.

Implements Panic Mode error recovery similar to Bison/YACC.
Automatically calculates synchronization tokens for each rule
using Follow Set analysis.
"""

from typing import Dict, Set, Tuple
from parser import Grammar, Rule


class RecoveryAnalyzer:
    """Analyzes grammar to compute synchronization tokens."""

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.rules_by_name = {r.name: r for r in grammar.rules}
        self.tokens_by_name = {t.name: t for t in grammar.tokens}
        self.follow_sets: Dict[str, Set[str]] = {}
        self.first_sets: Dict[str, Set[str]] = {}
        self.sync_tokens: Dict[str, Set[str]] = {}

    def analyze(self) -> Dict[str, Set[str]]:
        """
        Perform complete analysis and return sync tokens for each rule.

        Returns:
            Dictionary mapping rule names to their synchronization tokens
        """
        self._compute_first_sets()
        self._compute_follow_sets()
        self._compute_sync_tokens()
        return self.sync_tokens

    def _compute_first_sets(self) -> None:
        """Compute FIRST sets for all rules using fixed-point algorithm."""
        # Initialize FIRST sets
        for token in self.grammar.tokens:
            self.first_sets[token.name] = {token.name}

        for rule in self.grammar.rules:
            self.first_sets[rule.name] = set()

        # Fixed-point iteration until convergence
        changed = True
        iterations = 0
        max_iterations = len(self.grammar.rules) * 2

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1

            for rule in self.grammar.rules:
                old_size = len(self.first_sets[rule.name])

                for expr in rule.expressions:
                    if not expr.terms:
                        # Empty production
                        continue

                    for term in expr.terms:
                        obj = term.object_related

                        # Skip literals for now
                        if obj.startswith("'") and obj.endswith("'"):
                            self.first_sets[rule.name].add(obj.strip("'"))
                            break

                        # Token or rule
                        if obj in self.first_sets:
                            self.first_sets[rule.name].update(self.first_sets[obj])
                            # If this term can't be nullable, stop
                            if obj not in self._nullable_symbols:
                                break

                if len(self.first_sets[rule.name]) > old_size:
                    changed = True

    def _compute_follow_sets(self) -> None:
        """Compute FOLLOW sets for all rules."""
        for rule in self.grammar.rules:
            self.follow_sets[rule.name] = set()

        # Start rule can be followed by end-of-input
        for rule in self.grammar.rules:
            if rule.is_start:
                self.follow_sets[rule.name].add("EOF")

        # Fixed-point iteration
        changed = True
        iterations = 0
        max_iterations = len(self.grammar.rules) * 3

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1

            for rule in self.grammar.rules:
                for expr in rule.expressions:
                    for i, term in enumerate(expr.terms):
                        obj = term.object_related

                        # Only process if it's a rule (not a token or literal)
                        if obj not in self.rules_by_name:
                            continue

                        old_size = len(self.follow_sets[obj])

                        # Look at what follows this term
                        for following_term in expr.terms[i + 1 :]:
                            following_obj = following_term.object_related

                            # Add FIRST of following term
                            if following_obj in self.first_sets:
                                self.follow_sets[obj].update(
                                    self.first_sets[following_obj]
                                )
                            elif following_obj.startswith("'"):
                                self.follow_sets[obj].add(following_obj.strip("'"))

                            # If following term is not nullable, stop
                            if following_obj not in self._nullable_symbols:
                                break
                        else:
                            # All remaining terms are nullable, add FOLLOW of rule
                            self.follow_sets[obj].update(self.follow_sets[rule.name])

                        if len(self.follow_sets[obj]) > old_size:
                            changed = True

    def _compute_sync_tokens(self) -> None:
        """Compute synchronization tokens for each rule."""
        for rule in self.grammar.rules:
            sync = set()

            # 1. FOLLOW of the rule
            sync.update(self.follow_sets.get(rule.name, set()))

            # 2. FIRST of each expression option
            for expr in rule.expressions:
                if expr.terms:
                    first_term = expr.terms[0]
                    obj = first_term.object_related

                    if obj in self.first_sets:
                        sync.update(self.first_sets[obj])
                    elif obj.startswith("'"):
                        sync.add(obj.strip("'"))

            # 3. Add FIRST tokens of all rules (for better recovery)
            for other_rule in self.grammar.rules:
                sync.update(self.first_sets.get(other_rule.name, set()))

            # Remove empty string if present
            sync.discard("")

            self.sync_tokens[rule.name] = sync

    @property
    def _nullable_symbols(self) -> Set[str]:
        """Returns set of symbols that can match empty input."""
        # For PEG, typically nothing is nullable
        # Unless explicitly marked (would need grammar extension)
        return set()

    def get_sync_tokens(self, rule_name: str) -> Set[str]:
        """Get synchronization tokens for a specific rule."""
        return self.sync_tokens.get(rule_name, set())

    def get_sync_tokens_for_all_rules(self) -> Dict[str, Set[str]]:
        """Get synchronization tokens for all rules."""
        return self.sync_tokens.copy()


class RecoveryStrategy:
    """Handles actual error recovery during parsing."""

    def __init__(
        self, tokens, sync_tokens: Dict[str, Set[str]], enable_recovery: bool = True
    ):
        """
        Initialize recovery strategy.

        Args:
            tokens: List of tokens from lexer
            sync_tokens: Dictionary of synchronization tokens per rule
            enable_recovery: Whether to enable recovery mode
        """
        self.tokens = tokens
        self.sync_tokens = sync_tokens
        self.enable_recovery = enable_recovery
        self.errors = []

    def skip_to_sync(self, current_pos: int, rule_name: str) -> int:
        """
        Skip tokens until finding a synchronization point.

        Args:
            current_pos: Current position in token stream
            rule_name: Name of the rule we're recovering from

        Returns:
            New position in token stream
        """
        if not self.enable_recovery:
            return current_pos

        sync_set = self.sync_tokens.get(rule_name, set())
        if not sync_set:
            return current_pos

        # Skip tokens until we find one in sync_set
        while current_pos < len(self.tokens):
            token = self.tokens[current_pos]
            if token.type in sync_set:
                break
            current_pos += 1

        return current_pos

    def record_error(self, message: str, pos: int, expected: list):
        """Record an error for later reporting."""
        self.errors.append(
            {
                "message": message,
                "position": pos,
                "expected": expected,
                "token": self.tokens[pos] if pos < len(self.tokens) else None,
            }
        )

    def get_errors(self) -> list:
        """Get all recorded errors."""
        return self.errors.copy()
