import re
import sys


class ConstrictorFormatter:
    def __init__(self, content):
        self.content = content
        self.formatted = ""
        self.indent = "    "

    def format(self):
        # Split into lines and process
        lines = self.content.split("\n")

        # State machine
        in_tokens = False
        in_rule = False
        in_test = False
        in_check_guard = False

        output = []

        # Regexes
        grammar_start = re.compile(r"^\s*grammar\s+(\w+)\s*:")
        tokens_start = re.compile(r"^\s*tokens\s*:")
        rule_start = re.compile(r"^\s*(start\s+)?rule\s+(\w+)\s*:")
        test_start = re.compile(r"^\s*test\s+(\w+)(?:\s+(\w+))?\s*:")
        end_block = re.compile(r"^\s*end\b")
        check_start = re.compile(r"^\s*check\s+")
        then_keyword = re.compile(r"^\s*then\b")
        else_then_keyword = re.compile(r"^\s*else\s+then\b")

        # Track last non-empty line
        last_was_empty = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
                # Only add one empty line max
                if not last_was_empty and output:
                    output.append("")
                    last_was_empty = True
                continue

            last_was_empty = False

            # Comments
            if stripped.startswith("#"):
                # Preserve indentation level based on context
                indent_level = 1
                if in_check_guard:
                    indent_level = 4  # Deeper for check guard
                elif in_tokens or in_rule or in_test:
                    indent_level = 2
                output.append(self.indent * indent_level + stripped)
                continue

            # Grammar Start
            match = grammar_start.match(stripped)
            if match:
                output.append(f"grammar {match.group(1)}:")
                continue

            # Tokens Start
            match = tokens_start.match(stripped)
            if match:
                in_tokens = True
                output.append(self.indent + "tokens:")
                continue

            # Rule Start
            match = rule_start.match(stripped)
            if match:
                in_rule = True
                in_check_guard = False
                prefix = "start " if match.group(1) else ""
                if output and not output[-1].strip():  # Already has empty line
                    pass
                else:
                    output.append("")  # Add space before rule
                output.append(self.indent + f"{prefix}rule {match.group(2)}:")
                continue

            # Test Start
            match = test_start.match(stripped)
            if match:
                in_test = True
                target = f" {match.group(2)}" if match.group(2) else ""
                if output and not output[-1].strip():  # Already has empty line
                    pass
                else:
                    output.append("")  # Add space before test
                output.append(self.indent + f"test {match.group(1)}{target}:")
                continue

            # End Block
            if end_block.match(stripped):
                in_check_guard = False
                if in_tokens:
                    in_tokens = False
                    output.append(self.indent + "end")
                elif in_rule:
                    in_rule = False
                    output.append(self.indent + "end")
                elif in_test:
                    in_test = False
                    output.append(self.indent + "end")
                else:
                    # End of grammar - should be unindented
                    output.append("end")
                continue

            # Content within blocks
            if in_tokens:
                # Format token: NAME: pattern
                # Handle 'skip'
                token_match = re.compile(r"^(\w+)\s*:\s*(skip\s+)?(.*)$").match(
                    stripped
                )
                if token_match:
                    name = token_match.group(1)
                    skip = "skip " if token_match.group(2) else ""
                    pattern = token_match.group(3)
                    output.append(self.indent * 2 + f"{name}: {skip}{pattern}")
                else:
                    output.append(self.indent * 2 + stripped)

            elif in_rule:
                # Check for check guard start
                if check_start.match(stripped):
                    in_check_guard = True
                    output.append(self.indent * 3 + stripped)
                    continue
                elif in_check_guard:
                    # Inside check guard
                    if then_keyword.match(stripped):
                        # Standalone 'then' keyword - keep at same level as check
                        output.append(self.indent * 3 + stripped)
                        continue
                    elif else_then_keyword.match(stripped):
                        # 'else then' keyword - keep at same level as check
                        output.append(self.indent * 3 + stripped)
                        continue
                    elif stripped.startswith("|"):
                        # New expression, end of check guard
                        in_check_guard = False
                        # Fall through to handle the expression
                    else:
                        # Code inside check guard (one more indent)
                        output.append(self.indent * 4 + stripped)
                        continue

                # If we're here and not in check guard, process as expression
                if not in_check_guard or stripped.startswith("|"):
                    in_check_guard = False  # Reset if we hit a new expression

                    # Format rule alternative: | ... -> ...
                    is_expression = (
                        "->" in stripped
                        or stripped.startswith("|")
                        or (
                            not stripped.startswith("#")
                            and not stripped.startswith("end")
                        )
                    )

                    if is_expression:
                        # Parse expression
                        if "->" in stripped:
                            parts = stripped.split("->", 1)
                            left = parts[0].strip()
                            right = parts[1].strip()
                        else:
                            left = stripped.strip()
                            right = "pass"  # Auto-add pass

                        # Ensure space after | if present
                        if left.startswith("|"):
                            left = "| " + left[1:].strip()

                        output.append(self.indent * 2 + f"{left} -> {right}")
                    else:
                        output.append(self.indent * 2 + stripped)

            elif in_test:
                # Format test case: "input" => Result
                if "=>" in stripped:
                    parts = stripped.split("=>", 1)
                    inp = parts[0].strip()
                    res = parts[1].strip()
                    output.append(self.indent * 2 + f"{inp} => {res}")
                else:
                    output.append(self.indent * 2 + stripped)

            else:
                # Top level unknown content
                output.append(stripped)

        return "\n".join(output)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            formatter = ConstrictorFormatter(content)
            formatted_code = formatter.format()

            # If --write flag is passed, overwrite file, else print to stdout
            if len(sys.argv) > 2 and sys.argv[2] == "--write":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(formatted_code)
            else:
                print(formatted_code)
        except Exception as e:
            print(f"Error formatting file: {e}", file=sys.stderr)
