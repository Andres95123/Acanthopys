from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parser import Grammar

from .common import generate_common_classes
from .ast import generate_ast_nodes
from .lexer import generate_lexer
from .parser import generate_parser
from utils.recovery import RecoveryAnalyzer


class CodeGenerator:
    def __init__(self, grammar: "Grammar", enable_recovery: bool = False):
        self.grammar = grammar
        self.literal_map = {}
        self.enable_recovery = enable_recovery
        self.sync_tokens = {}
        self._collect_literals()
        if enable_recovery:
            self._analyze_recovery()

    def _collect_literals(self):
        literals = set()
        for rule in self.grammar.rules:
            for expr in rule.expressions:
                for term in expr.terms:
                    obj = term.object_related
                    if obj.startswith("'") and obj.endswith("'"):
                        literals.add(obj.strip("'"))

        for i, lit in enumerate(sorted(literals)):
            self.literal_map[lit] = f"LITERAL_{i}"

    def _analyze_recovery(self):
        """Analyze grammar for error recovery synchronization tokens."""
        try:
            analyzer = RecoveryAnalyzer(self.grammar)
            self.sync_tokens = analyzer.analyze()
        except Exception:
            # If recovery analysis fails, continue without it
            self.sync_tokens = {}

    def generate(self) -> str:
        code = []
        code.append("import re")
        code.append("from dataclasses import dataclass")
        code.append("")

        # 1. Common classes (Token, Lexer base, Parser base)
        code.append(generate_common_classes())

        # 2. AST Nodes
        code.append(generate_ast_nodes(self.grammar))

        # 3. Lexer/Tokenizer
        code.append(generate_lexer(self.grammar, self.literal_map))

        # 4. Parser with optional recovery
        code.append(
            generate_parser(
                self.grammar,
                self.literal_map,
                enable_recovery=self.enable_recovery,
                sync_tokens=self.sync_tokens,
            )
        )

        return "\n".join(code)
