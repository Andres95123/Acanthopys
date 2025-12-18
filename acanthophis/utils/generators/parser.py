from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from parser import Grammar


def generate_parser(grammar: "Grammar", literal_map: Dict[str, str]) -> str:
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
    lines.append("        if token and (type_name is None or token.type == type_name):")
    lines.append("            self.pos += 1")
    lines.append("            return token")
    lines.append("        return None")
    lines.append("")
    lines.append("    def expect(self, type_name):")
    lines.append("        token = self.consume(type_name)")
    lines.append("        if not token:")
    lines.append("            raise ParseError(f'Expected {type_name} at {self.pos}')")
    lines.append("        return token")
    lines.append("")

    for rule in grammar.rules:
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
                        if any(r.name == t.object_related for r in grammar.rules)
                    ]

                    if len(rule_indices) == 1:
                        auto_capture_index = rule_indices[0]
                    else:
                        # Heuristic 2: If no rules (or multiple), try to find a single non-literal term
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

                obj = term.object_related

                # Heuristic: if it matches a rule name, call parse_Rule
                # Else assume it's a token type.
                is_rule = any(r.name == obj for r in grammar.rules)

                if is_rule:
                    lines.append(f"            {target} = self.parse_{obj}()")
                elif obj.startswith("'"):
                    # Literal handling
                    # We use the literal string as the token type
                    literal_val = obj.strip("'")
                    lines.append(f"            {target} = self.expect('{literal_val}')")
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
