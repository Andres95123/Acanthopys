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
                if stripped.startswith("|"):
                    # Split by ->
                    parts = stripped.split("->")
                    left = parts[0].strip()

                    # Format left side (terms)
                    # Ensure space after |
                    if left.startswith("|"):
                        left = "| " + left[1:].strip()

                    if len(parts) > 1:
                        right = parts[1].strip()
                        output.append(self.indent * 2 + f"{left} -> {right}")
                    else:
                        output.append(self.indent * 2 + left)
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
