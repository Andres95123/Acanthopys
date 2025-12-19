import re
import sys
import json
import os
from parser import Parser


class VenomLinter:
    def __init__(self, file_path, content=None):
        self.file_path = file_path
        self.diagnostics = []
        self.rules = {}
        self.tokens = {}
        self.token_patterns = {}
        self.start_rule = None
        self.ast_constructors = {}
        self.test_suites = {}

        if content is not None:
            self.content = content
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.content = f.read()
            except Exception as e:
                self.content = ""
                self.add_diagnostic(1, f"Error reading file: {e}", "Error")

    def add_diagnostic(self, line, message, severity="Error", code=None):
        diag = {
            "line": line,
            "message": f"[{severity}] {message}",
            "file": self.file_path,
            "severity": severity,
        }
        if code:
            diag["code"] = code
        self.diagnostics.append(diag)

    def _parse_structure(self):
        parser = Parser()
        try:
            grammars = parser.parse(self.content)
        except Exception as e:
            self.add_diagnostic(1, str(e), "Error")
            return

        if not grammars:
            self.add_diagnostic(
                1, "No grammar found", "Error", code="missing-grammar-name"
            )
            return

        grammar = grammars[0]

        # Tokens
        if not grammar.tokens:
            self.add_diagnostic(
                1, "Missing 'tokens:' block.", "Error", code="missing-tokens-block"
            )

        for token in grammar.tokens:
            self.tokens[token.name] = {
                "is_skip": token.skip,
                "pattern": token.pattern,
                "line": token.line,
            }
            self.token_patterns[token.name] = token.pattern

        # Rules
        for rule in grammar.rules:
            if rule.is_start:
                self.start_rule = rule.name

            calls = set()
            captures = []
            ast_nodes = []

            for expr in rule.expressions:
                # Captures
                for term in expr.terms:
                    if term.variable:
                        captures.append((term.variable, term.object_related))

                    # Calls
                    obj = term.object_related
                    if not (obj.startswith("'") and obj.endswith("'")):
                        calls.add(obj)

                # AST Nodes
                ast_match = re.search(r"(\w+)\s*\(([^)]*)\)", expr.return_object)
                if ast_match:
                    node_class = ast_match.group(1)
                    args = [
                        arg.strip()
                        for arg in ast_match.group(2).split(",")
                        if arg.strip()
                    ]
                    ast_nodes.append((node_class, args))

                    if node_class not in self.ast_constructors:
                        self.ast_constructors[node_class] = []

                    self.ast_constructors[node_class].append(
                        {"args": args, "line": rule.line}
                    )

            self.rules[rule.name] = {
                "calls": calls,
                "line": rule.line,
                "expressions": rule.expressions,
                "captures": captures,
                "ast_nodes": ast_nodes,
            }

        # Tests
        for test_suite in grammar.tests:
            target = test_suite.target_rule or self.start_rule
            if target:
                if target not in self.test_suites:
                    self.test_suites[target] = []
                self.test_suites[target].append(test_suite.name)

    def levenshtein_distance(self, s1, s2):
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def find_closest_match(self, word, candidates):
        """Find the closest match to word in candidates using Levenshtein distance."""
        if not candidates:
            return None

        min_distance = float("inf")
        closest = None

        for candidate in candidates:
            distance = self.levenshtein_distance(word.lower(), candidate.lower())
            if (
                distance < min_distance and distance <= 3
            ):  # Only suggest if distance is reasonable
                min_distance = distance
                closest = candidate

        return closest

    def check_undefined_rules(self):
        """Checks for rules or tokens that are used but not defined."""
        defined_rules = set(self.rules.keys())
        all_defined = defined_rules | set(self.tokens.keys())

        for rule_name, data in self.rules.items():
            for call in data["calls"]:
                if call not in all_defined:
                    suggestion = self.find_closest_match(call, all_defined)
                    message = f"Undefined reference: '{call}'"
                    if suggestion:
                        message += f". Did you mean '{suggestion}'?"

                    # Use rule line as fallback
                    found_line = data["line"]
                    self.add_diagnostic(found_line, message, code="undefined-reference")

    def check_unreachable_rules(self):
        """Detects rules that cannot be reached from the 'start rule'."""
        if not self.start_rule:
            if self.rules:
                first_rule = list(self.rules.keys())[0]
                self.add_diagnostic(
                    self.rules[first_rule]["line"],
                    "No 'start rule' defined. Using first rule as entry point.",
                    "Information",
                )
                self.start_rule = first_rule
            else:
                return

        reachable = set()

        def walk(name):
            if name in reachable or name not in self.rules:
                return
            reachable.add(name)
            for call in self.rules[name]["calls"]:
                if call in self.rules:
                    walk(call)

        walk(self.start_rule)

        for rule_name in self.rules:
            if rule_name not in reachable:
                self.add_diagnostic(
                    self.rules[rule_name]["line"],
                    f"Unreachable rule (Orphan): '{rule_name}'",
                    "Warning",
                    code="unreachable-rule",
                )

    def check_left_recursion(self):
        """
        Detects if a rule calls itself at the beginning (Left Recursion).

        NOTE: Acanthophis now supports direct left recursion via Warth's algorithm.
        This check is disabled/deprecated but kept for reference or potential future warnings about indirect recursion.
        """
        pass

    def check_naming_conventions(self):
        """Checks if Tokens are UPPERCASE and Rules are PascalCase."""
        for token, data in self.tokens.items():
            if not token.isupper():
                self.add_diagnostic(
                    data["line"],
                    f"Token '{token}' should be UPPERCASE.",
                    "Warning",
                    code="naming-convention-token",
                )

        for rule in self.rules:
            if not rule[0].isupper():
                self.add_diagnostic(
                    self.rules[rule]["line"],
                    f"Rule '{rule}' should start with an uppercase letter (PascalCase).",
                    "Warning",
                    code="naming-convention-rule",
                )

    def check_duplicate_definitions(self):
        # Check duplicate tokens
        token_section = re.search(r"tokens:(.*?)end", self.content, re.DOTALL)
        if token_section:
            token_names = re.findall(
                r"^\s*(\w+):", token_section.group(1), re.MULTILINE
            )
            seen = set()
            for name in token_names:
                if name in seen:
                    self.add_diagnostic(
                        1, f"Duplicate token definition: '{name}'", "Error"
                    )
                seen.add(name)

    def check_regex_validity(self):
        """Check if token regexes are valid python regexes."""
        for token_name, data in self.tokens.items():
            pattern = data["pattern"]
            try:
                re.compile(pattern)
            except re.error as e:
                self.add_diagnostic(
                    data["line"],
                    f"Invalid regex for token '{token_name}': {str(e)}",
                    "Error",
                )

    def check_token_shadowing(self):
        """Check if more general token patterns shadow more specific ones."""
        token_list = list(self.tokens.items())

        for i, (name1, data1) in enumerate(token_list):
            if data1["is_skip"]:
                continue

            pattern1 = data1["pattern"]

            # Try to compile the pattern
            try:
                regex1 = re.compile(pattern1)
            except:
                continue

            # Check against all following tokens
            for j in range(i + 1, len(token_list)):
                name2, data2 = token_list[j]
                pattern2 = data2["pattern"]

                # Check if pattern1 could match what pattern2 is supposed to match
                # This is a heuristic: if pattern2 is a literal or keyword, test if pattern1 matches it

                # Check if pattern2 is a simple literal (like 'if', 'while', etc.)
                if pattern2.startswith("'") or pattern2.startswith('"'):
                    # It's a literal
                    literal = pattern2.strip("'\"")
                    try:
                        if regex1.fullmatch(literal):
                            self.add_diagnostic(
                                data2["line"],
                                f"Token '{name2}' may be shadowed by earlier token '{name1}'. "
                                f"Token '{name1}' (line {data1['line']}) has a more general pattern that matches '{name2}'.",
                                "Warning",
                                code="token-shadowing",
                            )
                    except:
                        pass
                else:
                    # For complex patterns, check if pattern1 is more general
                    # Common case: [a-zA-Z_]\w* (identifier) shadows specific keywords
                    if pattern1 in [
                        r"[a-zA-Z_]\w*",
                        r"[a-zA-Z]+",
                        r"\w+",
                    ] and pattern2 not in [r"[a-zA-Z_]\w*", r"[a-zA-Z]+", r"\w+"]:
                        self.add_diagnostic(
                            data2["line"],
                            f"Token '{name2}' may be shadowed by earlier general token '{name1}' (line {data1['line']}). "
                            f"Consider moving '{name2}' before '{name1}'.",
                            "Warning",
                        )

    def check_unused_tokens(self):
        """Check for tokens that are not used in any rule and not marked as skip."""
        used_tokens = set()

        # Collect all tokens used in rules
        for rule_name, data in self.rules.items():
            for call in data["calls"]:
                if call in self.tokens:
                    used_tokens.add(call)

        # Check each token
        for token_name, data in self.tokens.items():
            if token_name not in used_tokens and not data["is_skip"]:
                self.add_diagnostic(
                    data["line"],
                    f"Token '{token_name}' is not used in any rule. "
                    f"Consider marking it as 'skip' if it should be ignored, or use it in a rule.",
                    "Warning",
                    code="unused-token",
                )

    def check_ast_constructor_consistency(self):
        """Check if AST constructors are used with consistent number of arguments."""
        for node_class, usages in self.ast_constructors.items():
            if len(usages) <= 1:
                continue

            arg_counts = {}
            for usage in usages:
                count = len(usage["args"])
                if count not in arg_counts:
                    arg_counts[count] = []
                arg_counts[count].append(usage["line"])

            if len(arg_counts) > 1:
                # Inconsistent usage
                counts_str = ", ".join(
                    [
                        f"{count} args (line {lines[0]})"
                        for count, lines in arg_counts.items()
                    ]
                )
                self.add_diagnostic(
                    usages[0]["line"],
                    f"Inconsistent usage of AST constructor '{node_class}'. "
                    f"Found different argument counts: {counts_str}",
                    "Warning",
                )

    def check_test_coverage(self):
        """Check if all rules have associated tests."""
        for rule_name, data in self.rules.items():
            if rule_name not in self.test_suites:
                self.add_diagnostic(
                    data["line"],
                    f"Rule '{rule_name}' has no associated tests. Your grammar might be fragile.",
                    "Information",
                    code="rule-missing-tests",
                )

    def check_unnecessary_captures(self):
        """Check for unnecessary captures (variables captured but not used)."""
        for rule_name, data in self.rules.items():
            for expr in data["expressions"]:
                if expr.return_object == "pass":
                    captures = [term.variable for term in expr.terms if term.variable]
                    if len(captures) > 1:
                        self.add_diagnostic(
                            data["line"],
                            f"Rule '{rule_name}' has multiple captures ({', '.join(captures)}) but uses '-> pass'. "
                            f"Consider removing unnecessary capture labels for cleaner grammar.",
                            "Information",
                        )

    def check_nullability_and_loops(self):
        """
        Detects potential infinite loops caused by nullable rules in loops.
        Since Acanthophis uses recursion for loops, we check for:
        1. Hidden Left Recursion: A -> B -> A where B is nullable.
        2. Nullable rules that might cause issues if used in future repetition operators.
        """
        # 1. Identify Nullable Rules
        nullable_rules = set()
        changed = True

        while changed:
            changed = False
            for rule_name, data in self.rules.items():
                if rule_name in nullable_rules:
                    continue

                for expr in data["expressions"]:
                    if not expr.terms:
                        nullable_rules.add(rule_name)
                        changed = True
                        break

                    is_nullable = True
                    for term in expr.terms:
                        obj = term.object_related
                        if obj.startswith("'") and obj.endswith("'"):
                            is_nullable = False
                            break
                        if obj in self.tokens:
                            is_nullable = False
                            break
                        if obj not in nullable_rules:
                            is_nullable = False
                            break

                    if is_nullable:
                        nullable_rules.add(rule_name)
                        changed = True
                        break

        # 2. Check for Hidden Left Recursion
        for rule_name, data in self.rules.items():
            for expr in data["expressions"]:
                for i, term in enumerate(expr.terms):
                    obj = term.object_related
                    if obj == rule_name:
                        # Found recursion. Check if everything before it is nullable.
                        prefix_nullable = True
                        for prev_term in expr.terms[:i]:
                            prev_obj = prev_term.object_related
                            if prev_obj not in nullable_rules:
                                prefix_nullable = False
                                break

                        if (
                            prefix_nullable and i > 0
                        ):  # i=0 is direct left recursion, handled elsewhere
                            self.add_diagnostic(
                                data["line"],
                                f"Hidden Left Recursion detected in '{rule_name}'. "
                                f"The term '{obj}' is reached without consuming input because previous terms are nullable. "
                                f"This will cause an infinite loop.",
                                "Error",
                            )

                    # If current term is not nullable, we stop checking this alternative for hidden recursion
                    if obj not in nullable_rules:
                        break

    def check_critical_backtracking(self):
        """
        Identifies rules that might cause excessive backtracking.
        Checks for common prefixes in alternatives.
        """
        for rule_name, data in self.rules.items():
            # Collect first terms of each alternative
            first_terms = []
            for expr in data["expressions"]:
                if not expr.terms:
                    continue

                first_term = expr.terms[0].object_related
                first_terms.append(first_term)

            # Check for duplicates
            seen = set()
            duplicates = set()
            for term in first_terms:
                if term in seen:
                    duplicates.add(term)
                seen.add(term)

            if duplicates:
                self.add_diagnostic(
                    data["line"],
                    f"Potential critical backtracking in '{rule_name}'. "
                    f"Alternatives share common prefixes: {', '.join(duplicates)}. "
                    f"This forces the parser to backtrack. Consider factoring out the common prefix.",
                    "Warning",
                )

    def lint(self):
        if not self.content:
            return self.diagnostics

        self._parse_structure()
        # print(f"DEBUG: Diagnostics after parse: {self.diagnostics}")
        self.check_undefined_rules()
        self.check_unreachable_rules()
        self.check_left_recursion()
        self.check_naming_conventions()
        self.check_duplicate_definitions()
        self.check_regex_validity()
        self.check_token_shadowing()
        self.check_unused_tokens()
        self.check_ast_constructor_consistency()
        self.check_test_coverage()
        self.check_unnecessary_captures()
        self.check_nullability_and_loops()
        self.check_critical_backtracking()
        return self.diagnostics


if __name__ == "__main__":
    if len(sys.argv) > 1:
        linter = VenomLinter(sys.argv[1])
        results = linter.lint()
        print(json.dumps(results, indent=2))
