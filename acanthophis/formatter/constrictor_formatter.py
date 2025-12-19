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

        output = []

        # Regexes
        grammar_start = re.compile(r"^\s*grammar\s+(\w+)\s*:")
        tokens_start = re.compile(r"^\s*tokens\s*:")
        rule_start = re.compile(r"^\s*(start\s+)?rule\s+(\w+)\s*:")
        test_start = re.compile(r"^\s*test\s+(\w+)(?:\s+(\w+))?\s*:")
        end_block = re.compile(r"^\s*end\b")

        # Buffer for empty lines to avoid excessive spacing
        empty_lines = 0

        for line in lines:
            stripped = line.strip()

            if not stripped:
                if empty_lines < 1:
                    output.append("")
                    empty_lines += 1
                continue

            empty_lines = 0

            # Comments
            if stripped.startswith("#"):
                # Preserve indentation level based on context
                if in_tokens or in_rule or in_test:
                    output.append(self.indent + stripped)
                else:
                    output.append(stripped)
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
                prefix = "start " if match.group(1) else ""
                output.append("")  # Add space before rule
                output.append(self.indent + f"{prefix}rule {match.group(2)}:")
                continue

            # Test Start
            match = test_start.match(stripped)
            if match:
                in_test = True
                target = f" {match.group(2)}" if match.group(2) else ""
                output.append("")  # Add space before test
                output.append(self.indent + f"test {match.group(1)}{target}:")
                continue

            # End Block
            if end_block.match(stripped):
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
                # Relaxed regex for token definition
                token_match = re.match(r"^(\w+)\s*:\s*(skip\s+)?(.*)$", stripped)
                if token_match:
                    name = token_match.group(1)
                    skip = "skip " if token_match.group(2) else ""
                    pattern = token_match.group(3)
                    output.append(self.indent * 2 + f"{name}: {skip}{pattern}")
                else:
                    output.append(self.indent * 2 + stripped)

            elif in_rule:
                # Format rule alternative: | ... -> ...
                # Check if it's an expression line (starts with | or is just terms)
                # Heuristic: if it contains '->' it's definitely an expression.
                # If it starts with '|', it's an expression.
                # If it doesn't start with '|' but we are in a rule, it might be the first expression (implicit |)

                is_expression = (
                    "->" in stripped
                    or stripped.startswith("|")
                    or (not stripped.startswith("#") and not stripped.startswith("end"))
                )

                if is_expression:
                    # Handle check guards
                    check_part = None
                    if " check " in stripped:
                        parts = stripped.split(" check ", 1)
                        stripped = parts[0].strip()
                        check_part = parts[1].strip()

                    if "->" in stripped:
                        parts = stripped.split("->")
                        left = parts[0].strip()
                        right = parts[1].strip()
                    else:
                        left = stripped.strip()
                        right = "pass"  # Auto-add pass

                    # Ensure space after | if present
                    if left.startswith("|"):
                        left = "| " + left[1:].strip()

                    output.append(self.indent * 2 + f"{left} -> {right}")

                    if check_part:
                        # Parse check guard: condition then code [else then code]
                        # Regex to split: (.+) then (.+) (else then (.+))?
                        # But 'else then' is optional.

                        # Simple split by ' then '
                        # Note: 'then' might be in code, but we assume standard usage

                        # Try to find 'else then' first
                        else_code = None
                        if " else then " in check_part:
                            parts = check_part.split(" else then ", 1)
                            check_part = parts[0].strip()
                            else_code = parts[1].strip()

                        if " then " in check_part:
                            parts = check_part.split(" then ", 1)
                            condition = parts[0].strip()
                            then_code = parts[1].strip()

                            output.append(self.indent * 3 + f"check {condition} then")
                            output.append(self.indent * 3 + f"{then_code}")

                            if else_code:
                                output.append(self.indent * 3 + "else then")
                                output.append(self.indent * 3 + f"{else_code}")
                        else:
                            # Fallback if malformed
                            output.append(self.indent * 3 + f"check {check_part}")

                else:
                    output.append(self.indent * 2 + stripped)

            elif in_test:
                # Format test case: "input" => Result
                if "=>" in stripped:
                    parts = stripped.split("=>")
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
