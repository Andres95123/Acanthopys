from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parser import Grammar

from .common import generate_common_classes
from .ast import generate_ast_nodes
from .lexer import generate_lexer
from .parser import generate_parser


class CodeGenerator:
    def __init__(self, grammar: "Grammar"):
        self.grammar = grammar
        self.literal_map = {}
        self._collect_literals()

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

        # 4. Parser
        code.append(generate_parser(self.grammar, self.literal_map))

        return "\n".join(code)
