from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from parser import Grammar


def generate_parser(
    grammar: "Grammar",
    literal_map: Dict[str, str],
    enable_recovery: bool = False,
    sync_tokens: Dict[str, set] = None,
) -> str:
    lines = []
    lines.append("class Parser:")
    lines.append("    def __init__(self, tokens, enable_recovery=False):")
    lines.append("        self.tokens = tokens")
    lines.append("        self.pos = 0")
    lines.append("        self.memo = {}")
    lines.append("        self.enable_recovery = enable_recovery")
    lines.append("        self.errors = []")
    lines.append(
        "        # Synchronization tokens for each rule (computed during generation)"
    )

    # Add synchronization token map if recovery is enabled
    if sync_tokens:
        lines.append("        self.sync_tokens = {")
        for rule_name, tokens_set in sync_tokens.items():
            tokens_repr = repr(sorted(list(tokens_set)))
            lines.append(f"            '{rule_name}': {tokens_repr},")
        lines.append("        }")
    else:
        lines.append("        self.sync_tokens = {}")

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
    lines.append("            found = self.current()")
    lines.append(
        "            msg = f'Expected {type_name}, found {found.type if found else \"EOF\"}'"
    )
    lines.append("            raise ParseError(msg, token=found, expected=[type_name])")
    lines.append("        return token")
    lines.append("")
    lines.append("    def skip_to_sync(self, rule_name, start_pos):")
    lines.append('        """Skip tokens until finding a synchronization point."""')
    lines.append("        if not self.enable_recovery:")
    lines.append("            return")
    lines.append("        ")
    lines.append("        sync_set = self.sync_tokens.get(rule_name, set())")
    lines.append("        if not sync_set:")
    lines.append("            return")
    lines.append("        ")
    lines.append("        while self.pos < len(self.tokens):")
    lines.append("            token = self.current()")
    lines.append("            if token and token.type in sync_set:")
    lines.append("                break")
    lines.append("            self.pos += 1")
    lines.append("")
    lines.append("    def add_error(self, error_msg, token=None, expected=None):")
    lines.append('        """Record an error for later reporting."""')
    lines.append("        if token is None:")
    lines.append("            token = self.current()")
    lines.append("        self.errors.append({")
    lines.append("            'message': error_msg,")
    lines.append("            'token': token,")
    lines.append("            'expected': expected or [],")
    lines.append("            'line': token.line if token else 0,")
    lines.append("            'column': token.column if token else 0,")
    lines.append("        })")
    lines.append("")
    lines.append("    def get_errors(self):")
    lines.append('        """Get all recorded errors."""')
    lines.append("        return self.errors.copy()")
    lines.append("")

    for rule in grammar.rules:
        lines.append(f"    def _parse_{rule.name}_body(self):")
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
                is_rule = any(r.name == obj for r in grammar.rules)

                if is_rule:
                    call_code = f"self.parse_{obj}()"
                elif obj.startswith("'"):
                    literal_val = obj.strip("'")
                    call_code = f"self.expect('{literal_val}')"
                else:
                    call_code = f"self.expect('{obj}')"

                if term.quantifier == "+":
                    lines.append(f"            # One or more {obj}")
                    lines.append(f"            {target} = []")
                    lines.append(f"            {target}.append({call_code})")
                    lines.append(f"            while True:")
                    lines.append(f"                _save = self.pos")
                    lines.append(f"                try:")
                    lines.append(f"                    _item = {call_code}")
                    lines.append(f"                    {target}.append(_item)")
                    lines.append(
                        f"                    if self.enable_recovery and isinstance(_item, ErrorNode) and _save == self.pos:"
                    )
                    lines.append(f"                        if self.consume() is None:")
                    lines.append(f"                            break")
                    lines.append(f"                except ParseError:")
                    lines.append(f"                    self.pos = _save")
                    lines.append(f"                    break")

                elif term.quantifier == "*":
                    lines.append(f"            # Zero or more {obj}")
                    lines.append(f"            {target} = []")
                    lines.append(f"            while True:")
                    lines.append(f"                _save = self.pos")
                    lines.append(f"                try:")
                    lines.append(f"                    _item = {call_code}")
                    lines.append(f"                    {target}.append(_item)")
                    lines.append(
                        f"                    if self.enable_recovery and isinstance(_item, ErrorNode) and _save == self.pos:"
                    )
                    lines.append(f"                        if self.consume() is None:")
                    lines.append(f"                            break")
                    lines.append(f"                except ParseError:")
                    lines.append(f"                    self.pos = _save")
                    lines.append(f"                    break")

                elif term.quantifier == "?":
                    lines.append(f"            # Optional {obj}")
                    lines.append(f"            _save = self.pos")
                    lines.append(f"            try:")
                    lines.append(f"                {target} = {call_code}")
                    lines.append(f"            except ParseError:")
                    lines.append(f"                self.pos = _save")
                    lines.append(f"                {target} = None")

                else:
                    lines.append(f"            {target} = {call_code}")

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

            if expr.check_guard:
                lines.append(f"            # Check Guard")
                lines.append(f"            if {expr.check_guard.condition}:")
                lines.append(f"                {expr.check_guard.then_code}")
                if expr.check_guard.else_code:
                    lines.append(f"            else:")
                    lines.append(f"                {expr.check_guard.else_code}")

            # Success handling for memoization
            lines.append(f"            return res")

            lines.append(f"        except ParseError as e:")
            lines.append(f"            pass")

        # Failure handling for memoization with recovery support
        lines.append(f"        # All alternatives failed for {rule.name}")
        lines.append(f"        found = self.current()")
        lines.append(
            f"        error = ParseError('No alternative matched for {rule.name}', token=found)"
        )
        lines.append(f"        ")
        lines.append(f"        if self.enable_recovery:")
        lines.append(f"            if found is None:")
        lines.append(f"                raise error")
        lines.append(f"            self.add_error(error.message, token=found)")
        lines.append(f"            self.skip_to_sync('{rule.name}', start_pos)")
        lines.append(f"            # Return ErrorNode for recovery mode")
        lines.append(f"            error_node = ErrorNode(")
        lines.append(
            f"                error_message='No alternative matched for {rule.name}',"
        )
        lines.append(
            f"                tokens_consumed=self.tokens[start_pos:self.pos],"
        )
        lines.append(f"                token=found")
        lines.append(f"            )")
        lines.append(f"            return error_node")
        lines.append(f"        ")
        lines.append(f"        raise error")
        lines.append("")

        lines.append(f"    def parse_{rule.name}(self):")
        lines.append(f"        key = ('{rule.name}', self.pos)")
        lines.append(f"        ")
        lines.append(f"        if key in self.memo:")
        lines.append(f"            res = self.memo[key]")
        lines.append(f"            if isinstance(res, LeftRecursion):")
        lines.append(f"                res.detected = True")
        lines.append(f"                if res.seed is not None:")
        lines.append(f"                    val, end_pos = res.seed")
        lines.append(f"                    self.pos = end_pos")
        lines.append(f"                    return val")
        lines.append(f"                else:")
        lines.append(f"                    raise ParseError('Left recursion detected')")
        lines.append(f"            ")
        lines.append(f"            val, end_pos = res")
        lines.append(f"            if isinstance(val, Exception):")
        lines.append(f"                raise val")
        lines.append(f"            self.pos = end_pos")
        lines.append(f"            return val")
        lines.append(f"        ")
        lines.append(f"        rec = LeftRecursion()")
        lines.append(f"        self.memo[key] = rec")
        lines.append(f"        start_pos = self.pos")
        lines.append(f"        ")
        lines.append(f"        try:")
        lines.append(f"            res = self._parse_{rule.name}_body()")
        lines.append(f"        except ParseError as e:")
        lines.append(f"            if not rec.detected:")
        lines.append(f"                self.memo[key] = (e, start_pos)")
        lines.append(f"                raise e")
        lines.append(f"            res = None")
        lines.append(f"        ")
        lines.append(f"        if rec.detected:")
        lines.append(f"            if res is None:")
        lines.append(f"                del self.memo[key]")
        lines.append(f"                raise ParseError('Failed after recursion')")
        lines.append(f"            ")
        lines.append(f"            rec.seed = (res, self.pos)")
        lines.append(f"            last_end_pos = self.pos")
        lines.append(f"            ")
        lines.append(f"            while True:")
        lines.append(f"                self.pos = start_pos")
        lines.append(f"                try:")
        lines.append(f"                    new_res = self._parse_{rule.name}_body()")
        lines.append(f"                    if self.pos > last_end_pos:")
        lines.append(f"                        last_end_pos = self.pos")
        lines.append(f"                        rec.seed = (new_res, self.pos)")
        lines.append(f"                        res = new_res")
        lines.append(f"                    else:")
        lines.append(f"                        break")
        lines.append(f"                except ParseError:")
        lines.append(f"                    break")
        lines.append(f"            ")
        lines.append(f"            self.pos = last_end_pos")
        lines.append(f"            self.memo[key] = (res, self.pos)")
        lines.append(f"            return res")
        lines.append(f"        ")
        lines.append(f"        self.memo[key] = (res, self.pos)")
        lines.append(f"        return res")
        lines.append("")

    return "\n".join(lines)
