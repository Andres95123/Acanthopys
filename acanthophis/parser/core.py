import ast
import re
from .models import Token, Term, Expression, Rule, TestCase, TestSuite, Grammar
from .constants import (
    GRAMMAR_PATTERN,
    TOKENS_BLOCK_PATTERN,
    RULE_PATTERN,
    TOKEN_LINE_PATTERN,
    EXPRESSION_OPTION_PATTERN,
    TERM_PATTERN,
    TEST_BLOCK_PATTERN,
    TEST_CASE_START_PATTERN,
)


class Parser:
    def __init__(self) -> None:
        pass

    def parse(self, text: str) -> list[Grammar]:
        grammars: list[Grammar] = []

        grammar_matches = list(GRAMMAR_PATTERN.finditer(text))

        if not grammar_matches:
            # Fallback or empty check? The original code raised exception if grammar_groups is None,
            # but findall returns empty list if not found.
            pass

        for grammar_match in grammar_matches:
            grammar_name = grammar_match.group(1)
            grammar_text = grammar_match.group(2)
            grammar_start_offset = grammar_match.start(2)

            token_block_matches = list(TOKENS_BLOCK_PATTERN.finditer(grammar_text))
            if not token_block_matches:
                raise Exception(
                    "No tokens detected, add 'tokens:' to your file and start adding tokens 'NAME: PATTERN' under the tokens header"
                )

            tokens: list[Token] = []
            for token_block_match in token_block_matches:
                token_body = token_block_match.group(1)
                token_body_start_offset = (
                    grammar_start_offset + token_block_match.start(1)
                )

                for token_match in TOKEN_LINE_PATTERN.finditer(token_body):
                    name = token_match.group(1)
                    skip = token_match.group(2)
                    pattern = token_match.group(3)

                    abs_offset = token_body_start_offset + token_match.start()
                    line = text.count("\n", 0, abs_offset) + 1

                    tokens.append(
                        Token(
                            name,
                            skip is not None and skip.strip() != "",
                            pattern.strip(),
                            line,
                        )
                    )

            rules_matches = list(RULE_PATTERN.finditer(grammar_text))
            rules: list[Rule] = []
            start_rules_count = 0

            for rule_match in rules_matches:
                start_keyword = rule_match.group(1)
                rule_name = rule_match.group(2)
                rule_body = rule_match.group(3)

                is_start = bool(start_keyword and start_keyword.strip())
                if is_start:
                    start_rules_count += 1

                rule_start_offset = grammar_start_offset + rule_match.start()
                line = text.count("\n", 0, rule_start_offset) + 1

                expressions: list[Expression] = []
                for expresion_line, return_object in EXPRESSION_OPTION_PATTERN.findall(
                    rule_body
                ):
                    terms: list[Term] = []
                    for var_name, term_name, quantifier in TERM_PATTERN.findall(
                        expresion_line
                    ):
                        terms.append(Term(term_name, var_name, quantifier or None))
                    expressions.append(Expression(terms, return_object.strip()))
                rules.append(Rule(expressions, rule_name, is_start, line))

            if start_rules_count > 1:
                raise Exception(
                    f"Grammar '{grammar_name}': Multiple start rules defined. Only one rule can be marked with 'start'."
                )

            defined_tokens = {t.name for t in tokens}
            defined_rules = {r.name for r in rules}

            for rule in rules:
                for expr in rule.expressions:
                    for term in expr.terms:
                        obj = term.object_related
                        if obj.startswith("'") and obj.endswith("'"):
                            continue

                        if obj not in defined_rules and obj not in defined_tokens:
                            raise Exception(
                                f"Grammar '{grammar_name}': Undefined token or rule '{obj}' used in rule '{rule.name}'."
                            )

            if start_rules_count == 0 and rules:
                pass

            test_matches = list(TEST_BLOCK_PATTERN.finditer(grammar_text))
            tests: list[TestSuite] = []
            for test_match in test_matches:
                test_name = test_match.group(1)
                target_rule = test_match.group(2)
                test_body = test_match.group(3)

                target_rule = target_rule.strip() if target_rule else None
                test_body_start_offset = grammar_start_offset + test_match.start(3)

                cases: list[TestCase] = []

                starts = list(TEST_CASE_START_PATTERN.finditer(test_body))

                if not starts:
                    lines = [
                        l.strip()
                        for l in test_body.split("\n")  # noqa: E741
                        if l.strip() and not l.strip().startswith("#")
                    ]
                    if lines:
                        raise Exception(
                            f"Grammar '{grammar_name}', test suite '{test_name}': "
                            f"Invalid test syntax or no tests found. Tests must follow the format:\n"
                            f'  "input" => Success|Fail|Yields(...)'
                        )

                for i, match in enumerate(starts):
                    raw_input = (
                        match.group(1) if match.group(1) is not None else match.group(2)
                    )
                    start_idx = match.end()

                    if i + 1 < len(starts):
                        end_idx = starts[i + 1].start()
                    else:
                        end_idx = len(test_body)

                    expectation = test_body[start_idx:end_idx].strip()

                    abs_offset = test_body_start_offset + match.start()
                    line = text.count("\n", 0, abs_offset) + 1

                    try:
                        if match.group(1) is not None:
                            input_text = ast.literal_eval(f'"{raw_input}"')
                        else:
                            input_text = ast.literal_eval(f"'{raw_input}'")
                    except Exception as e:
                        raise Exception(
                            f"Grammar '{grammar_name}', test suite '{test_name}': "
                            f"Failed to parse test input string: {raw_input}\n"
                            f"Error: {e}"
                        )

                    exp_type = "Success"
                    exp_val = None

                    if expectation == "Success":
                        exp_type = "Success"
                    elif expectation == "Fail":
                        exp_type = "Fail"
                    elif expectation.startswith("Yields"):
                        exp_type = "Yields"
                        first_paren = expectation.find("(")
                        last_paren = expectation.rfind(")")

                        if (
                            first_paren == -1
                            or last_paren == -1
                            or last_paren < first_paren
                        ):
                            raise Exception(
                                f"Grammar '{grammar_name}', test suite '{test_name}': "
                                f"Invalid Yields syntax - must be Yields(...). Found: {expectation}"
                            )

                        exp_val = expectation[first_paren + 1 : last_paren]

                        exp_val = " ".join(exp_val.split())

                        if not exp_val.strip() and "..." not in expectation:
                            raise Exception(
                                f"Grammar '{grammar_name}', test suite '{test_name}': "
                                f"Yields() is empty - you must specify the expected AST structure"
                            )
                    else:
                        raise Exception(
                            f"Grammar '{grammar_name}', test suite '{test_name}': "
                            f"Invalid test expectation: '{expectation}'. "
                            f"Must be 'Success', 'Fail', or 'Yields(...)'"
                        )

                    cases.append(TestCase(input_text, exp_type, exp_val, line))
                tests.append(TestSuite(test_name, cases, target_rule))

            grammars.append(Grammar(grammar_name, tokens, rules, tests))

        return grammars
