class Token:
    def __init__(self, name: str, skip: bool, pattern: str, line: int = 0) -> None:
        self.name = name
        self.skip = skip
        self.pattern = pattern
        self.line = line


class Term:
    def __init__(
        self, object_related: str, variable: str, quantifier: str = None
    ) -> None:
        self.object_related = object_related
        self.variable = variable
        self.quantifier = quantifier


class CheckGuard:
    def __init__(self, condition: str, then_code: str, else_code: str = None) -> None:
        self.condition = condition
        self.then_code = then_code
        self.else_code = else_code


class Expression:
    def __init__(
        self, terms: list[Term], return_object: str, check_guard: CheckGuard = None
    ) -> None:
        self.terms = terms
        self.return_object = return_object
        self.check_guard = check_guard


class Rule:
    def __init__(
        self,
        expressions: list[Expression],
        name: str,
        is_start: bool = False,
        line: int = 0,
    ) -> None:
        self.expressions = expressions
        self.name = name
        self.is_start = is_start
        self.line = line


class TestCase:
    def __init__(
        self,
        input_text: str,
        expectation: str,
        expected_value: str = None,  # type: ignore
        line: int = 0,
    ) -> None:
        self.input_text = input_text
        self.expectation = expectation
        self.expected_value = expected_value
        self.line = line


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
