import re
import ast


class Token:
    def __init__(self, name: str, skip: bool, pattern: str) -> None:
        self.name = name
        self.skip = skip
        self.pattern = pattern


class Term:
    def __init__(self, object_related: str, variable: str) -> None:
        self.object_related = object_related
        self.variable = variable


class Expression:
    def __init__(self, terms: list[Term], return_object: str) -> None:
        self.terms = terms
        self.return_object = return_object


class Rule:
    def __init__(
        self, expressions: list[Expression], name: str, is_start: bool = False
    ) -> None:
        self.expressions = expressions
        self.name = name
        self.is_start = is_start


class TestCase:
    def __init__(
        self,
        input_text: str,
        expectation: str,
        expected_value: str = None,  # type: ignore
    ) -> None:
        self.input_text = input_text
        self.expectation = expectation
        self.expected_value = expected_value


class TestSuite:
    def __init__(
        self,
        name: str,
        cases: list[TestCase],
        target_rule: str = None,  # type: ignore
    ) -> None:
        self.name = name
        self.cases = cases
        self.target_rule = target_rule


class Grammar:
    def __init__(
        self,
        name: str,
        tokens: list[Token],
        rules: list[Rule],
        tests: list[TestSuite] = [],
    ) -> None:
        self.name = name
        self.tokens = tokens
        self.rules = rules
        self.tests = tests


GRAMMAR_PATTERN = re.compile(
    r"""
    (?ms)               
    ^\s*grammar\s+      
    (\w+)               
    \s*:\s*             
    (.*?)               
    ^end\b              
    [^\n]*              
""",
    re.VERBOSE,
)

TOKENS_BLOCK_PATTERN = re.compile(
    r"""
    (?ms)
    ^\s*tokens\s*:\s*   
    (.*?)               
    ^\s*end\b           
    [^\n]*              
""",
    re.VERBOSE,
)

RULE_PATTERN = re.compile(
    r"""
    (?ms)
    ^\s*
    (start\s+)?         
    rule\s+             
    (\w+)               
    \s*:\s*             
    (.*?)               
    ^\s*end\b           
    [^\n]*              
""",
    re.VERBOSE,
)

TOKEN_LINE_PATTERN = re.compile(
    r"""
    (?m)
    ^\s*                
    (\w+)               
    \s*:\s*             
    (skip\s+)?          
    ([^#\n]+)           
    (?:\s*\#.*)?        
    $
""",
    re.VERBOSE,
)

EXPRESSION_OPTION_PATTERN = re.compile(
    r"""
    (?m)
    ^\s*\|\s*           
    (.*?)\s*            
    ->\s*               
    ([^#\n]+)           
    (?:\s*\#.*)?        
    $
""",
    re.VERBOSE,
)

TERM_PATTERN = re.compile(
    r"""
    (?:                 
        (\w+)           
        :               
    )?
    (                   
        \w+             
        |               
        '[^']*'         
    )
    """,
    re.VERBOSE,
)

TEST_BLOCK_PATTERN = re.compile(
    r"""
    (?ms)
    ^\s*test\s+         
    (\w+)               
    (?:
        \s+             
        (\w+)           
    )?
    \s*:\s*             
    (.*?)               
    ^\s*end\b           
    [^\n]*              
""",
    re.VERBOSE,
)

TEST_CASE_START_PATTERN = re.compile(
    r"""
    ^\s*
    (?:
        "([^"]*)"       
        |
        '([^']*)'       
    )
    \s*=>\s*            
    """,
    re.VERBOSE | re.MULTILINE,
)


class Parser:
    def __init__(self) -> None:
        pass

    def parse(self, text: str) -> list[Grammar]:
        grammars: list[Grammar] = []

        grammar_groups = GRAMMAR_PATTERN.findall(text)

        for grammar_name, grammar_text in grammar_groups:
            if grammar_groups is None:
                raise Exception(
                    "Any grammar section detected, add 'grammar NAME:' to your .acantho"
                )

            token_groups = TOKENS_BLOCK_PATTERN.findall(grammar_text)
            if token_groups is None:
                raise Exception(
                    "No tokens detected, add 'tokens:' to your file and start adding tokens 'NAME: PATTERN' under the tokens header"
                )

            tokens: list[Token] = []
            for token_text in token_groups:
                token_groups = TOKEN_LINE_PATTERN.findall(token_text)
                for name, skip, pattern in token_groups:
                    tokens.append(Token(name, skip != "", pattern.strip()))

            rules_groups = RULE_PATTERN.findall(grammar_text)
            rules: list[Rule] = []
            start_rules_count = 0

            for start_keyword, rule_name, rule_text in rules_groups:
                is_start = bool(start_keyword.strip())
                if is_start:
                    start_rules_count += 1

                expressions: list[Expression] = []
                for expresion_line, return_object in EXPRESSION_OPTION_PATTERN.findall(
                    rule_text
                ):
                    terms: list[Term] = []
                    for var_name, term_name in TERM_PATTERN.findall(expresion_line):
                        terms.append(Term(term_name, var_name))
                    expressions.append(Expression(terms, return_object.strip()))
                rules.append(Rule(expressions, rule_name, is_start))

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

            test_groups = TEST_BLOCK_PATTERN.findall(grammar_text)
            tests: list[TestSuite] = []
            for test_name, target_rule, test_body in test_groups:
                target_rule = target_rule.strip() if target_rule else None
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

                    cases.append(TestCase(input_text, exp_type, exp_val))  # type: ignore
                tests.append(TestSuite(test_name, cases, target_rule))  # type: ignore

            grammars.append(Grammar(grammar_name, tokens, rules, tests))

        return grammars
