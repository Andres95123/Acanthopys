from .acanthopys_parser import Grammar, Rule, Expression, Term
import re


class CodeGenerator:
    def __init__(self, grammar: Grammar):
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
        code.append(self._generate_common_classes())

        # 2. AST Nodes
        code.append(self._generate_ast_nodes())

        # 3. Lexer/Tokenizer
        code.append(self._generate_lexer())

        # 4. Parser
        code.append(self._generate_parser())

        return "\n".join(code)

    def _generate_common_classes(self) -> str:
        return """
@dataclass(frozen=True)
class Token:
    type: str
    value: str
    line: int = 0
    column: int = 0
    
    def __float__(self):
        return float(self.value)
        
    def __int__(self):
        return int(self.value)
        
    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{self.value!r}"

class ParseError(Exception):
    pass
"""

    def _generate_ast_nodes(self) -> str:
        # Collect all node names from rules
        node_names = set()
        for rule in self.grammar.rules:
            for expr in rule.expressions:
                ret = expr.return_object
                if ret == "pass":
                    continue
                # Check if it's a call like NumberNode(float(value))
                if "(" in ret:
                    name = ret.split("(")[0]
                    node_names.add(name)
                else:
                    node_names.add(ret)

        lines = []
        for name in sorted(node_names):
            lines.append(f"@dataclass")
            lines.append(f"class {name}:")
            # We don't know the fields statically easily without analyzing all usages
            # For now, let's make it generic or try to infer.
            # To keep it simple and flexible, we can use **kwargs or just pass
            # But dataclass requires fields.
            # Let's just make a simple class that accepts anything for now,
            # or maybe just a pass if we don't use dataclass for them.
            # Actually, let's not use dataclass for AST nodes if we don't know fields.
            # Or better, just generate a generic __init__.
            lines.pop()  # remove @dataclass
            lines.pop()  # remove class definition

            lines.append(f"class {name}:")
            lines.append(f"    def __init__(self, *args, **kwargs):")
            lines.append(f"        self.args = args")
            lines.append(f"        for k, v in kwargs.items():")
            lines.append(f"            setattr(self, k, v)")
            lines.append(f"    def __repr__(self):")
            lines.append(f"        params = []")
            lines.append(f"        if self.args:")
            lines.append(f"            params.extend([repr(a) for a in self.args])")
            lines.append(f"        for k, v in self.__dict__.items():")
            lines.append(f"            if k != 'args':")
            lines.append(f"                params.append(repr(v))")
            lines.append(f"        return f'{name}({{', '.join(params)}})'")
            lines.append("")

        return "\n".join(lines)

    def _generate_lexer(self) -> str:
        lines = []
        lines.append("class Lexer:")
        lines.append("    def __init__(self, text):")
        lines.append("        self.text = text")
        lines.append("        self.pos = 0")
        lines.append("        self.tokens = []")
        lines.append("        self.tokenize()")
        lines.append("")
        lines.append("    def tokenize(self):")
        lines.append("        # Regex patterns")

        lines.append("        token_specs = [")

        # We need to map group names to token types because group names must be identifiers
        group_map = {}

        for token in self.grammar.tokens:
            group_name = f"TOKEN_{token.name}"
            group_map[group_name] = token.name
            lines.append(f"            ('{group_name}', r'{token.pattern}'),")

        # Add literals
        for lit, group_name in self.literal_map.items():
            # Escape regex special chars in literal
            escaped = re.escape(lit)
            group_map[group_name] = (
                lit  # Use literal value as token type? Or the group name?
            )
            # If we use literal value as token type, then expect('(') works.
            # But expect('TOKEN_plus') works for tokens.
            # Let's use the literal value as the token type for literals.
            lines.append(f"            ('{group_name}', r'{escaped}'),")

        lines.append("            ('MISMATCH', r'.'),")
        lines.append("        ]")
        lines.append("")
        lines.append(f"        group_map = {group_map}")
        lines.append("")
        lines.append("        # Compile regex")
        lines.append(
            "        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specs)"
        )
        lines.append("        get_token = re.compile(tok_regex).match")
        lines.append("")

        # Identify skipped tokens
        skipped_tokens = [t.name for t in self.grammar.tokens if t.skip]
        lines.append(f"        skipped_tokens = {repr(set(skipped_tokens))}")

        lines.append("        line_num = 1")
        lines.append("        line_start = 0")
        lines.append("        mo = get_token(self.text)")
        lines.append("        while mo is not None:")
        lines.append("            kind = mo.lastgroup")
        lines.append("            value = mo.group(kind)")
        lines.append("            if kind == 'MISMATCH':")
        lines.append(
            "                raise ParseError(f'Unexpected character {value!r} on line {line_num}')"
        )
        lines.append("            ")
        lines.append("            # Map back to token type")
        lines.append("            token_type = group_map.get(kind, kind)")
        lines.append("            ")
        lines.append("            if token_type in skipped_tokens:")
        lines.append("                pass")
        lines.append("            else:")
        lines.append(
            "                self.tokens.append(Token(token_type, value, line_num, mo.start() - line_start))"
        )
        lines.append("            ")
        lines.append("            # Update position")
        lines.append("            pos = mo.end()")
        lines.append("            mo = get_token(self.text, pos)")
        lines.append("            if pos == len(self.text): break")
        lines.append("")

        return "\n".join(lines)

    def _generate_parser(self) -> str:
        lines = []
        lines.append("class Parser:")
        lines.append("    def __init__(self, tokens):")
        lines.append("        self.tokens = tokens")
        lines.append("        self.pos = 0")
        lines.append("        self.memo = {}")
        lines.append("")
        lines.append("    def current(self):")
        lines.append("        if self.pos < len(self.tokens):")
        lines.append("            return self.tokens[self.pos]")
        lines.append("        return None")
        lines.append("")
        lines.append("    def consume(self, type_name=None):")
        lines.append("        token = self.current()")
        lines.append(
            "        if token and (type_name is None or token.type == type_name):"
        )
        lines.append("            self.pos += 1")
        lines.append("            return token")
        lines.append("        return None")
        lines.append("")
        lines.append("    def expect(self, type_name):")
        lines.append("        token = self.consume(type_name)")
        lines.append("        if not token:")
        lines.append(
            "            raise ParseError(f'Expected {type_name} at {self.pos}')"
        )
        lines.append("        return token")
        lines.append("")

        for rule in self.grammar.rules:
            lines.append(f"    def parse_{rule.name}(self):")
            lines.append(f"        # Memoization check")
            lines.append(f"        key = ('{rule.name}', self.pos)")
            lines.append(f"        if key in self.memo:")
            lines.append(f"            res, end_pos = self.memo[key]")
            lines.append(f"            if isinstance(res, Exception):")
            lines.append(f"                raise res")
            lines.append(f"            self.pos = end_pos")
            lines.append(f"            return res")
            lines.append("")
            lines.append(f"        start_pos = self.pos")

            for i, expr in enumerate(rule.expressions):
                lines.append(f"        # Option {i}")
                lines.append(f"        self.pos = start_pos")
                lines.append(f"        try:")

                # Generate code for terms
                vars_collected = []

                # Determine which term to capture if no variables are present and it is a pass rule
                auto_capture_index = -1
                if expr.return_object == "pass":
                    # Check if we have explicit variables
                    has_vars = any(t.variable for t in expr.terms)
                    if not has_vars:
                        # Heuristic 1: If there is exactly one Rule, capture it.
                        rule_indices = [
                            i
                            for i, t in enumerate(expr.terms)
                            if any(
                                r.name == t.object_related for r in self.grammar.rules
                            )
                        ]

                        if len(rule_indices) == 1:
                            auto_capture_index = rule_indices[0]
                        else:
                            # Heuristic 2: If no rules (or multiple), try to find a single non-literal term
                            # But be careful with tokens. If we have LPAREN Expr RPAREN, Expr is a rule, so Heuristic 1 catches it.
                            # If we have LPAREN INT RPAREN (where INT is token), rule_indices is empty.
                            # non_literal_indices would be 3.
                            # If we have just INT (token), non_literal_indices is 1.

                            non_literal_indices = [
                                i
                                for i, t in enumerate(expr.terms)
                                if not (
                                    t.object_related.startswith("'")
                                    and t.object_related.endswith("'")
                                )
                            ]

                            if len(non_literal_indices) == 1:
                                auto_capture_index = non_literal_indices[0]
                            elif len(expr.terms) == 1:
                                # Fallback for single literal term
                                auto_capture_index = 0

                for i, term in enumerate(expr.terms):
                    if term.variable:
                        target = term.variable
                        vars_collected.append(target)
                    elif i == auto_capture_index:
                        target = "term_val"
                        vars_collected.append(target)
                    else:
                        target = "_"

                    # Check if term.object_related is a token or a rule
                    # We need to know which are tokens and which are rules.
                    # Usually rules start with Uppercase or we check against rule names.
                    # But tokens are lower case in the example.

                    obj = term.object_related
                    if obj.startswith("'") and obj.endswith("'"):
                        # Literal
                        literal = obj.strip("'")
                        # We need to match a token with this value or type?
                        # The grammar uses token names like 'plus', 'mult'.
                        # But also literals like '(' in Factor.
                        # If it's a literal, we might need to match a token type that corresponds to it,
                        # or if the lexer produces specific token types for literals.
                        # For now, assume we match by value or type if it matches a token name.
                        pass

                    # Heuristic: if it matches a rule name, call parse_Rule
                    # Else assume it's a token type.
                    is_rule = any(r.name == obj for r in self.grammar.rules)

                    if is_rule:
                        lines.append(f"            {target} = self.parse_{obj}()")
                    elif obj.startswith("'"):
                        # Literal handling
                        # We use the literal string as the token type
                        literal_val = obj.strip("'")
                        lines.append(
                            f"            {target} = self.expect('{literal_val}')"
                        )
                    else:
                        # Token
                        lines.append(f"            {target} = self.expect('{obj}')")

                # Return object
                ret = expr.return_object
                if ret == "pass":
                    # If pass, we usually return the child if there's only one, or None?
                    # "pass eleva el hijo sin crear nodo nuevo"
                    # If we have variables, return the first one?
                    # Usually 'pass' in this context means return the value of the child.
                    # If there is a variable named 'child' or 'inner', return it.
                    # Or just return the last parsed value?
                    # Let's look at the grammar: | child:Term -> pass
                    # | '(' inner:Expression ')' -> pass
                    # So we return the variable.

                    # Find the variable to return
                    # If there is only one variable, return it.
                    if vars_collected:
                        lines.append(f"            res = {vars_collected[0]}")  # Naive
                    else:
                        lines.append(f"            res = None")
                else:
                    # Construct the node
                    # If it's a call like NumberNode(float(value))
                    if "(" in ret:
                        # It's a python expression using the variables
                        lines.append(f"            res = {ret}")
                    else:
                        # It's a class name, pass vars as kwargs
                        args = ", ".join(f"{v}={v}" for v in vars_collected if v != "_")
                        lines.append(f"            res = {ret}({args})")

                # Success handling for memoization
                lines.append(f"            self.memo[key] = (res, self.pos)")
                lines.append(f"            return res")

                lines.append(f"        except ParseError:")
                lines.append(f"            pass")

            # Failure handling for memoization
            lines.append(
                f"        error = ParseError('No alternative matched for {rule.name}')"
            )
            lines.append(f"        self.memo[key] = (error, start_pos)")
            lines.append(f"        raise error")
            lines.append("")

        return "\n".join(lines)
