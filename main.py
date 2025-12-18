import argparse
import sys
import os
from utils.acanthopys_parser import Parser
from utils.code_generator import CodeGenerator
from lang.file_texts import AUTOMATIC_GENERATED_TEXT

# ANSI Colors
CYAN = "\033[96m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
PURPLE = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"


def log_info(msg):
    print(f"{CYAN}{BOLD}[INFO]{RESET} {msg}")


def log_success(msg):
    print(f"{GREEN}{BOLD}[SUCCESS]{RESET} {msg}")


def log_error(msg):
    print(f"{RED}{BOLD}[ERROR]{RESET} {msg}")


def log_warn(msg):
    print(f"{PURPLE}{BOLD}[WARN]{RESET} {msg}")


def match_with_wildcard(result_repr, expected_pattern):
    """
    Match a result representation with a pattern that may contain '...' wildcards.
    '...' inside a class constructor (e.g., AdditionNode(...)) matches any content.
    """
    import re

    # Escape special regex characters except for the wildcard placeholder
    # First, replace '...' with a unique placeholder
    placeholder = "<<<WILDCARD>>>"
    pattern = expected_pattern.replace("...", placeholder)

    # Escape regex special characters
    pattern = re.escape(pattern)

    # Replace the placeholder with a regex that matches anything (non-greedy)
    pattern = pattern.replace(placeholder, r".*?")

    # Ensure we match the entire string
    pattern = f"^{pattern}$"

    return re.match(pattern, result_repr) is not None


def run_tests_in_memory(grammar, code):
    log_info(f"Running integrated tests for grammar: {grammar.name}")

    # Create a new scope to execute the generated code
    scope = {}
    try:
        exec(code, scope)
    except SyntaxError as e:
        log_error(f"Failed to compile generated parser code: {e}")
        # Print context around the error
        lines = code.split("\n")
        start = max(0, e.lineno - 3)
        end = min(len(lines), e.lineno + 2)
        print(f"{YELLOW}Context:{RESET}")
        for i in range(start, end):
            prefix = f"{RED}>>{RESET} " if i + 1 == e.lineno else "   "
            print(f"{prefix}{i + 1:4d}: {lines[i]}")
        return False
    except Exception as e:
        log_error(f"Failed to execute generated parser code: {e}")
        return False

    Lexer = scope.get("Lexer")
    ParserClass = scope.get("Parser")
    ParseError = scope.get("ParseError")

    if not Lexer or not ParserClass:
        log_error("Could not find Lexer or Parser class in generated code.")
        return False

    failed_count = 0
    total_count = 0

    # Determine default start rule
    default_start_rule = None
    start_rules = [r for r in grammar.rules if r.is_start]

    if len(start_rules) == 1:
        default_start_rule = start_rules[0].name
    elif len(start_rules) == 0:
        if grammar.rules:
            default_start_rule = grammar.rules[0].name
            log_warn(
                f"No start rule defined for grammar '{grammar.name}'. Using first rule '{default_start_rule}' as default."
            )
            log_warn("Recommendation: Mark your entry rule with 'start rule RuleName:'")
    else:
        # This should be caught by parser, but just in case
        log_error(f"Multiple start rules defined for grammar '{grammar.name}'.")
        return False

    for suite in grammar.tests:
        print(f"\n  {BOLD}Test Suite: {suite.name}{RESET}")

        # Determine rule for this suite
        suite_rule_name = suite.target_rule if suite.target_rule else default_start_rule

        if not suite_rule_name:
            log_error(f"No rule available to test in suite '{suite.name}'.")
            return False

        for case in suite.cases:
            total_count += 1
            input_text = case.input_text

            try:
                lexer = Lexer(input_text)
                parser = ParserClass(lexer.tokens)

                parse_method = getattr(parser, f"parse_{suite_rule_name}", None)

                if not parse_method:
                    log_error(f"Rule 'parse_{suite_rule_name}' not found in parser.")
                    return False

                result = parse_method()

                if case.expectation == "Success":
                    print(f"    {GREEN}✔{RESET} {input_text} => Success")
                elif case.expectation == "Fail":
                    print(
                        f"    {RED}✘{RESET} {input_text} => Expected Fail but got Success"
                    )
                    failed_count += 1
                elif case.expectation == "Yields":
                    result_repr = repr(result)
                    # Check if expected value contains wildcard
                    if "..." in case.expected_value:
                        if match_with_wildcard(result_repr, case.expected_value):
                            print(
                                f"    {GREEN}✔{RESET} {input_text} => Yields match (with wildcard)"
                            )
                        else:
                            print(
                                f"    {RED}✘{RESET} {input_text} => Expected Yields({case.expected_value}) but got {result_repr}"
                            )
                            failed_count += 1
                    else:
                        if result_repr == case.expected_value:
                            print(f"    {GREEN}✔{RESET} {input_text} => Yields match")
                        else:
                            print(
                                f"    {RED}✘{RESET} {input_text} => Expected Yields({case.expected_value}) but got {result_repr}"
                            )
                            failed_count += 1

            except Exception as e:
                # Check if it is a ParseError (which might be defined in scope)
                is_parse_error = (
                    isinstance(e, ParseError)
                    if ParseError
                    else "ParseError" in str(type(e))
                )

                if case.expectation == "Fail" and is_parse_error:
                    print(f"    {GREEN}✔{RESET} {input_text} => Fail (as expected)")
                else:
                    # Provide context about where the error occurred
                    print(f"    {RED}✘{RESET} {input_text} => Unexpected error: {e}")
                    if "lexer" in locals() and hasattr(lexer, "tokens"):
                        print(
                            f"      {YELLOW}Tokens parsed:{RESET} {[str(t.value) for t in lexer.tokens[:10]]}"
                        )
                        if len(lexer.tokens) > 10:
                            print(f"      ... ({len(lexer.tokens) - 10} more tokens)")
                    if is_parse_error:
                        print(
                            f"      {YELLOW}Hint:{RESET} The input was tokenized correctly, but the parser couldn't match any rule."
                        )
                        print(
                            f"      Check that your grammar rules can handle this sequence of tokens."
                        )
                    failed_count += 1

    print("")
    if failed_count > 0:
        log_error(f"Tests failed: {failed_count}/{total_count}")
        return False

    log_success(f"All {total_count} tests passed!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Acanthopys: PEG Parser Generator")
    parser.add_argument("input", help="Input .acantho grammar file")
    parser.add_argument("-o", "--output", help="Output directory", default=".")
    parser.add_argument(
        "--no-tests", action="store_true", help="Disable integrated tests execution"
    )
    parser.add_argument(
        "--tests",
        action="store_true",
        help="Run only tests without generating parser file",
    )

    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output
    no_tests = args.no_tests
    only_tests = args.tests

    if not os.path.exists(input_path):
        log_error(f"Input file not found: {input_path}")
        sys.exit(1)

    log_info(f"Reading grammar from {input_path}...")

    try:
        with open(input_path, "r", encoding="utf-8") as file:
            content = file.read()

        acantho_parser = Parser()
        try:
            grammars = acantho_parser.parse(content)
        except Exception as e:
            log_error(f"Failed to parse grammar file '{input_path}':")
            log_error(f"  {e}")
            sys.exit(1)

        if not grammars:
            log_warn("No grammars found in file.")
            return

        for grammar in grammars:
            log_info(f"Generating parser for grammar: {grammar.name}")
            generator = CodeGenerator(grammar)
            code = generator.generate()

            # Run tests
            if grammar.tests:
                if no_tests:
                    log_warn(
                        f"Skipping tests for {grammar.name}. It is highly recommended to run tests to ensure parser correctness."
                    )
                else:
                    if not run_tests_in_memory(grammar, code):
                        log_error(
                            f"Aborting generation for {grammar.name} due to test failures."
                        )
                        sys.exit(1)
            else:
                log_warn(f"No tests defined for {grammar.name}. Skipping verification.")

            if only_tests:
                log_info(
                    f"Tests passed for {grammar.name}. Skipping file generation (--tests flag active)."
                )
                continue

            output_file = os.path.join(output_dir, f"{grammar.name}_parser.py")
            with open(output_file, "w") as file:
                file.write(f"{AUTOMATIC_GENERATED_TEXT}\n{code}")

            log_success(f"Parser written to {output_file}")

    except Exception as e:
        log_error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
