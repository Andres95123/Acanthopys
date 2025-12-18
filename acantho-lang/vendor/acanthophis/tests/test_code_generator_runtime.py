import pytest
from parser import Token, Term, Expression, Rule, Grammar
from utils.generators import CodeGenerator


class TestCodeGeneratorRuntime:
    def _simple_grammar(self) -> Grammar:
        # tokens: NUMBER: \d+ ; WS: skip \s+
        tokens = [
            Token("NUMBER", False, r"\d+"),
            Token("WS", True, r"\s+"),
            Token("PLUS", False, r"\+"),
        ]

        # start rule Expr:
        #   | left:Term PLUS right:Term -> Add
        #   | t:Term -> pass
        # end
        # rule Term:
        #   | n:NUMBER -> Number
        # end
        expr1 = Expression(
            terms=[Term("Term", "left"), Term("PLUS", ""), Term("Term", "right")],
            return_object="Add",
        )
        expr2 = Expression(
            terms=[Term("Term", "t")],
            return_object="pass",
        )
        term_expr = Expression(terms=[Term("NUMBER", "n")], return_object="Number")

        rules = [
            Rule([expr1, expr2], name="Expr", is_start=True),
            Rule([term_expr], name="Term", is_start=False),
        ]
        return Grammar("RuntimeTest", tokens, rules, tests=[])

    def test_generate_and_execute(self):
        grammar = self._simple_grammar()
        code = CodeGenerator(grammar).generate()

        scope = {}
        exec(code, scope)
        Lexer = scope["Lexer"]
        Parser = scope["Parser"]

        # 1 + 2 should parse
        lexer = Lexer("1 + 2")
        parser = Parser(lexer.tokens)
        res = parser.parse_Expr()

        assert str(res) == "Add(Number('1'), Number('2'))"
