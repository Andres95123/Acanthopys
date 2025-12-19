from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Any, Dict, TYPE_CHECKING

try:
    # When imported as part of the package
    from ..utils.logging import Logger, Ansi  # type: ignore
except Exception:  # pragma: no cover - fallback for test-time local imports
    # When tests import this module as top-level (tests run from package root)
    from utils.logging import Logger, Ansi  # type: ignore

if TYPE_CHECKING:  # Only for type hints; avoids runtime import issues
    from ..parser import Grammar  # type: ignore


def match_with_wildcard(result_repr: str, expected_pattern: str) -> bool:
    placeholder = "<<<WILDCARD>>>"
    pattern = expected_pattern.replace("...", placeholder)
    pattern = re.escape(pattern)
    pattern = pattern.replace(placeholder, r".*?")
    pattern = f"^{pattern}$"
    return re.match(pattern, result_repr) is not None


def run_tests_in_memory(
    grammar: "Grammar", code: str, logger: Logger | None = None
) -> bool:
    logger = logger or Logger()
    logger.info(f"Running integrated tests for grammar: {grammar.name}")

    scope: Dict[str, Any] = {}
    try:
        exec(code, scope)
    except SyntaxError as e:
        logger.error(f"Failed to compile generated parser code: {e}")
        lines = code.split("\n")
        start = max(0, (e.lineno or 1) - 3)
        end = min(len(lines), (e.lineno or 1) + 2)
        logger.hint("Context:")
        for i in range(start, end):
            prefix = ">> " if i + 1 == e.lineno else "   "
            print(f"{prefix}{i + 1:4d}: {lines[i]}")
        return False
    except Exception as e:
        logger.error(f"Failed to execute generated parser code: {e}")
        return False

    Lexer = scope.get("Lexer")
    ParserClass = scope.get("Parser")
    ParseError = scope.get("ParseError")

    if not Lexer or not ParserClass:
        logger.error("Could not find Lexer or Parser class in generated code.")
        return False

    failed_count = 0
    total_count = 0

    # Determine default start rule
    default_start_rule = None
    start_rules = [r for r in grammar.rules if getattr(r, "is_start", False)]
    if len(start_rules) == 1:
        default_start_rule = start_rules[0].name
    elif len(start_rules) == 0:
        if grammar.rules:
            default_start_rule = grammar.rules[0].name
            logger.warn(
                f"No start rule defined for grammar '{grammar.name}'. Using first rule '{default_start_rule}' as default."
            )
            logger.warn(
                "Recommendation: Mark your entry rule with 'start rule RuleName:'"
            )
        else:
            logger.error(f"No rules defined in grammar '{grammar.name}'.")
            return False
    else:
        logger.info(
            f"Multiple start rules defined for grammar '{grammar.name}'. Suites must specify target rule."
        )

    for suite in grammar.tests:
        print(f"\n  Test Suite: {suite.name}")

        suite_rule_name = suite.target_rule if suite.target_rule else default_start_rule
        if not suite_rule_name:
            logger.error(f"No rule available to test in suite '{suite.name}'.")
            return False

        for case in suite.cases:
            total_count += 1
            input_text = case.input_text

            try:
                lexer = Lexer(input_text)
                parser = ParserClass(lexer.tokens)
                parse_method = getattr(parser, f"parse_{suite_rule_name}", None)
                if not parse_method:
                    logger.error(f"Rule 'parse_{suite_rule_name}' not found in parser.")
                    return False

                result = parse_method()

                # Check for unconsumed tokens (EOF check)
                # Only if result is not None (successful parse)
                if result is not None:
                    current_token = parser.current()
                    if current_token is not None:
                        # If there are tokens left, it's a failure unless we expected a failure
                        # But wait, if we expected "Fail", catching the exception below handles it.
                        # If we expected "Success" or "Yields", this is a failure.
                        raise ParseError(
                            f"Expected EOF, found {current_token.type}",
                            token=current_token,
                        )

                if case.expectation == "Success":
                    print(f"    {Ansi.GREEN}✔{Ansi.RESET} {input_text} => Success")
                elif case.expectation == "Fail":
                    print(
                        f"    {Ansi.RED}✘{Ansi.RESET} {input_text} => Expected Fail but got Success"
                    )
                    failed_count += 1
                elif case.expectation == "Yields":
                    result_repr = repr(result)
                    if "..." in (case.expected_value or ""):
                        if match_with_wildcard(result_repr, case.expected_value):
                            print(
                                f"    {Ansi.GREEN}✔{Ansi.RESET} {input_text} => Yields match (with wildcard)"
                            )
                        else:
                            print(
                                f"    {Ansi.RED}✘{Ansi.RESET} {input_text} => Expected Yields({case.expected_value}) but got {result_repr}"
                            )
                            failed_count += 1
                    else:
                        if result_repr == case.expected_value:
                            print(
                                f"    {Ansi.GREEN}✔{Ansi.RESET} {input_text} => Yields match"
                            )
                        else:
                            print(
                                f"    {Ansi.RED}✘{Ansi.RESET} {input_text} => Expected Yields({case.expected_value}) but got {result_repr}"
                            )
                            failed_count += 1

            except Exception as e:  # noqa: BLE001 - we want DX here
                is_parse_error = (
                    isinstance(e, ParseError)
                    if ParseError
                    else "ParseError" in str(type(e))
                )
                if case.expectation == "Fail" and is_parse_error:
                    print(
                        f"    {Ansi.GREEN}✔{Ansi.RESET} {input_text} => Fail (as expected)"
                    )
                else:
                    print(
                        f"    {Ansi.RED}✘{Ansi.RESET} {input_text} => Unexpected error: {e}"
                    )
                    if "lexer" in locals() and hasattr(lexer, "tokens"):
                        logger.hint(
                            f"Tokens parsed: {[str(t.value) for t in lexer.tokens[:10]]}"
                        )
                        if len(lexer.tokens) > 10:
                            logger.hint(f"... ({len(lexer.tokens) - 10} more tokens)")
                    if is_parse_error:
                        logger.hint(
                            "The input was tokenized correctly, but the parser couldn't match any rule."
                        )
                        logger.hint(
                            "Check that your grammar rules can handle this sequence of tokens."
                        )
                    failed_count += 1

    print("")
    if failed_count > 0:
        logger.error(f"Tests failed: {failed_count}/{total_count}")
        return False

    logger.success(f"All {total_count} tests passed!")
    return True
