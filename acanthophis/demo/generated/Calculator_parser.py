import re
from dataclasses import dataclass


from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass(frozen=True)
class Token:
    type: str
    value: str
    line: int = 0
    column: int = 0

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{self.value!r}"

    def __len__(self):
        return len(self.value)


class ParseError(Exception):
    """Exception raised when parsing fails."""

    def __init__(self, message: str, token=None, expected: list = None):
        super().__init__(message)
        self.message = message
        self.token = token
        self.expected = expected or []
        self.line = token.line if token else 0
        self.column = token.column if token else 0

    def __str__(self):
        loc = f"line {self.line}, col {self.column}"
        return f"{self.message} at {loc}"


@dataclass
class ParseResult:
    """Result of a parse operation containing the AST and any errors."""

    ast: Any
    errors: List[ParseError]
    tokens: List[Token]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def unwrap(self):
        """Returns the AST if valid, otherwise raises the first error."""
        if self.errors:
            raise self.errors[0]
        return self.ast


class ErrorNode:
    """Represents an error in the parse tree for recovery mode."""

    def __init__(
        self,
        error_message: str = "",
        token=None,
        tokens_consumed: list = None,
        expected: list = None,
    ):
        self.error_message = error_message
        self.token = token
        self.tokens_consumed = tokens_consumed or []
        self.expected = expected or []
        self.line = token.line if token else 0
        self.column = token.column if token else 0

    def __repr__(self):
        return f"ErrorNode(message={self.error_message!r}, line={self.line}, col={self.column})"

    def __str__(self):
        return f"<error at {self.line}:{self.column}: {self.error_message}>"


class LeftRecursion:
    def __init__(self):
        self.detected = False
        self.seed = None


class AdditionNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"AdditionNode({', '.join(params)})"


class AssignmentNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"AssignmentNode({', '.join(params)})"


class ConditionalNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"ConditionalNode({', '.join(params)})"


class DeclarationNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"DeclarationNode({', '.join(params)})"


class DivisionNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"DivisionNode({', '.join(params)})"


class EqualNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"EqualNode({', '.join(params)})"


class ForLoopNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"ForLoopNode({', '.join(params)})"


class GreaterThanNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"GreaterThanNode({', '.join(params)})"


class GreaterThanOrEqualNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"GreaterThanOrEqualNode({', '.join(params)})"


class IdentifierNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"IdentifierNode({', '.join(params)})"


class LessThanNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"LessThanNode({', '.join(params)})"


class LessThanOrEqualNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"LessThanOrEqualNode({', '.join(params)})"


class LogicValueNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"LogicValueNode({', '.join(params)})"


class ModulusNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"ModulusNode({', '.join(params)})"


class MultiplicationNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"MultiplicationNode({', '.join(params)})"


class NotEqualNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"NotEqualNode({', '.join(params)})"


class NumberNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"NumberNode({', '.join(params)})"


class RangeNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"RangeNode({', '.join(params)})"


class SubtractionNode:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != "args":
                params.append(repr(v))
        return f"SubtractionNode({', '.join(params)})"


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.tokens = []
        self.tokenize()

    def tokenize(self):
        # Regex patterns
        token_specs = [
            ("TOKEN_comment", r"//.*|/\*([^*]|\*+[^*/])*\*+/"),
            ("TOKEN_IF_KW", r"\bif\b"),
            ("TOKEN_THEN_KW", r"\bthen\b"),
            ("TOKEN_ELIF_KW", r"\belif\b"),
            ("TOKEN_ELSE_KW", r"\belse\b"),
            ("TOKEN_FOR_KW", r"\bfor\b"),
            ("TOKEN_in_kw", r"\bin\b"),
            ("TOKEN_do_kw", r"\bdo\b"),
            ("TOKEN_range_op", r"\.\."),
            ("TOKEN_primitive_type", r"\b(int|float|bool|string)\b"),
            ("TOKEN_number", r"\d+(\.\d+)?"),
            ("TOKEN_logic_value", r"\b(true|false)\b"),
            ("TOKEN_gte", r">="),
            ("TOKEN_lte", r"<="),
            ("TOKEN_eq", r"=="),
            ("TOKEN_neq", r"!="),
            ("TOKEN_gt", r">"),
            ("TOKEN_lt", r"<"),
            ("TOKEN_ASSIGN", r"\="),
            ("TOKEN_add", r"\+"),
            ("TOKEN_subtract", r"-"),
            ("TOKEN_multiply", r"\*"),
            ("TOKEN_divide", r"\/"),
            ("TOKEN_modulus", r"\%"),
            ("TOKEN_lparen", r"\("),
            ("TOKEN_rparen", r"\)"),
            ("TOKEN_colon", r":"),
            ("TOKEN_separator", r";"),
            ("TOKEN_WHITESPACE", r"\s+"),
            ("TOKEN_IDENTIFIER", r"[a-zA-Z_]\w*"),
            ("MISMATCH", r"."),
        ]

        group_map = {
            "TOKEN_comment": "comment",
            "TOKEN_IF_KW": "IF_KW",
            "TOKEN_THEN_KW": "THEN_KW",
            "TOKEN_ELIF_KW": "ELIF_KW",
            "TOKEN_ELSE_KW": "ELSE_KW",
            "TOKEN_FOR_KW": "FOR_KW",
            "TOKEN_in_kw": "in_kw",
            "TOKEN_do_kw": "do_kw",
            "TOKEN_range_op": "range_op",
            "TOKEN_primitive_type": "primitive_type",
            "TOKEN_number": "number",
            "TOKEN_logic_value": "logic_value",
            "TOKEN_gte": "gte",
            "TOKEN_lte": "lte",
            "TOKEN_eq": "eq",
            "TOKEN_neq": "neq",
            "TOKEN_gt": "gt",
            "TOKEN_lt": "lt",
            "TOKEN_ASSIGN": "ASSIGN",
            "TOKEN_add": "add",
            "TOKEN_subtract": "subtract",
            "TOKEN_multiply": "multiply",
            "TOKEN_divide": "divide",
            "TOKEN_modulus": "modulus",
            "TOKEN_lparen": "lparen",
            "TOKEN_rparen": "rparen",
            "TOKEN_colon": "colon",
            "TOKEN_separator": "separator",
            "TOKEN_WHITESPACE": "WHITESPACE",
            "TOKEN_IDENTIFIER": "IDENTIFIER",
        }

        # Compile regex
        tok_regex = "|".join("(?P<%s>%s)" % pair for pair in token_specs)
        get_token = re.compile(tok_regex).match

        skipped_tokens = {"WHITESPACE", "comment"}
        line_num = 1
        line_start = 0
        mo = get_token(self.text)
        while mo is not None:
            kind = mo.lastgroup
            value = mo.group(kind)
            if kind == "MISMATCH":
                raise ParseError(f"Unexpected character {value!r} on line {line_num}")

            # Map back to token type
            token_type = group_map.get(kind, kind)

            if token_type in skipped_tokens:
                pass
            else:
                self.tokens.append(
                    Token(token_type, value, line_num, mo.start() - line_start)
                )

            # Update position
            pos = mo.end()
            mo = get_token(self.text, pos)
            if pos == len(self.text):
                break


class Parser:
    def __init__(self, tokens, enable_recovery=False):
        self.tokens = tokens
        self.pos = 0
        self.memo = {}
        self.enable_recovery = enable_recovery
        self.errors = []
        # Synchronization tokens for each rule (computed during generation)
        self.sync_tokens = {
            "Block": [
                "ELIF_KW",
                "ELSE_KW",
                "EOF",
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "logic_value",
                "lparen",
                "number",
            ],
            "Declaration": [
                "ELIF_KW",
                "ELSE_KW",
                "EOF",
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "logic_value",
                "lparen",
                "number",
            ],
            "Assignment": [
                "ELIF_KW",
                "ELSE_KW",
                "EOF",
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "logic_value",
                "lparen",
                "number",
            ],
            "Operand": [
                "ELIF_KW",
                "ELSE_KW",
                "EOF",
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "THEN_KW",
                "add",
                "divide",
                "do_kw",
                "eq",
                "gt",
                "gte",
                "logic_value",
                "lparen",
                "lt",
                "lte",
                "modulus",
                "multiply",
                "neq",
                "number",
                "range_op",
                "rparen",
                "subtract",
            ],
            "Expression": [
                "ELIF_KW",
                "ELSE_KW",
                "EOF",
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "THEN_KW",
                "logic_value",
                "lparen",
                "number",
            ],
            "Arithmetic": [
                "ELIF_KW",
                "ELSE_KW",
                "EOF",
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "THEN_KW",
                "do_kw",
                "eq",
                "gt",
                "gte",
                "logic_value",
                "lparen",
                "lt",
                "lte",
                "neq",
                "number",
                "range_op",
                "rparen",
            ],
            "Term": [
                "ELIF_KW",
                "ELSE_KW",
                "EOF",
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "THEN_KW",
                "add",
                "do_kw",
                "eq",
                "gt",
                "gte",
                "logic_value",
                "lparen",
                "lt",
                "lte",
                "neq",
                "number",
                "range_op",
                "rparen",
                "subtract",
            ],
            "Factor": [
                "ELIF_KW",
                "ELSE_KW",
                "EOF",
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "THEN_KW",
                "add",
                "divide",
                "do_kw",
                "eq",
                "gt",
                "gte",
                "logic_value",
                "lparen",
                "lt",
                "lte",
                "modulus",
                "multiply",
                "neq",
                "number",
                "range_op",
                "rparen",
                "subtract",
            ],
            "Comparison": [
                "ELIF_KW",
                "ELSE_KW",
                "EOF",
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "THEN_KW",
                "logic_value",
                "lparen",
                "number",
            ],
            "Conditional": [
                "ELIF_KW",
                "ELSE_KW",
                "EOF",
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "logic_value",
                "lparen",
                "number",
            ],
            "Range": [
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "do_kw",
                "logic_value",
                "lparen",
                "number",
            ],
            "ForLoop": [
                "ELIF_KW",
                "ELSE_KW",
                "EOF",
                "FOR_KW",
                "IDENTIFIER",
                "IF_KW",
                "logic_value",
                "lparen",
                "number",
            ],
        }

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, type_name=None):
        token = self.current()
        if token and (type_name is None or token.type == type_name):
            self.pos += 1
            return token
        return None

    def expect(self, type_name):
        token = self.consume(type_name)
        if not token:
            found = self.current()
            msg = f"Expected {type_name}, found {found.type if found else 'EOF'}"
            raise ParseError(msg, token=found, expected=[type_name])
        return token

    def skip_to_sync(self, rule_name, start_pos):
        """Skip tokens until finding a synchronization point."""
        if not self.enable_recovery:
            return

        sync_set = self.sync_tokens.get(rule_name, set())
        if not sync_set:
            return

        while self.pos < len(self.tokens):
            token = self.current()
            if token and token.type in sync_set:
                break
            self.pos += 1

    def add_error(self, error_msg, token=None, expected=None):
        """Record an error for later reporting."""
        if token is None:
            token = self.current()
        self.errors.append(
            {
                "message": error_msg,
                "token": token,
                "expected": expected or [],
                "line": token.line if token else 0,
                "column": token.column if token else 0,
            }
        )

    def get_errors(self):
        """Get all recorded errors."""
        return self.errors.copy()

    def error(self, msg):
        raise ParseError(msg, token=self.current())

    def _parse_Block_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            stmt = self.parse_Declaration()
            res = stmt
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 1
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            stmt = self.parse_Assignment()
            res = stmt
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 2
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            stmt = self.parse_Conditional()
            res = stmt
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 3
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            stmt = self.parse_ForLoop()
            res = stmt
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for Block
        found = self.current()
        msg = "No alternative matched for Block"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = True
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("Block", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for Block",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_Block(self):
        key = ("Block", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_Block_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Block_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    def _parse_Declaration_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            id = self.expect("IDENTIFIER")
            _ = self.expect("colon")
            primitive = self.expect("primitive_type")
            res = DeclarationNode(id, primitive)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for Declaration
        found = self.current()
        msg = "No alternative matched for Declaration"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = not failed_at_start
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("Declaration", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for Declaration",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_Declaration(self):
        key = ("Declaration", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_Declaration_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Declaration_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    def _parse_Assignment_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            id = self.expect("IDENTIFIER")
            _ = self.expect("ASSIGN")
            val = self.parse_Expression()
            res = AssignmentNode(id, val)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for Assignment
        found = self.current()
        msg = "No alternative matched for Assignment"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = not failed_at_start
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("Assignment", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for Assignment",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_Assignment(self):
        key = ("Assignment", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_Assignment_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Assignment_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    def _parse_Operand_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            n = self.expect("number")
            res = NumberNode(float(n))
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 1
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            lv = self.expect("logic_value")
            res = LogicValueNode(lv.value == "true")
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 2
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            id = self.expect("IDENTIFIER")
            res = IdentifierNode(id)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for Operand
        found = self.current()
        msg = "No alternative matched for Operand"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = not failed_at_start
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("Operand", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for Operand",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_Operand(self):
        key = ("Operand", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_Operand_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Operand_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    def _parse_Expression_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            term_val = self.parse_Comparison()
            res = term_val
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 1
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            term_val = self.parse_Arithmetic()
            res = term_val
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for Expression
        found = self.current()
        msg = "No alternative matched for Expression"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = not failed_at_start
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("Expression", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for Expression",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_Expression(self):
        key = ("Expression", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_Expression_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Expression_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    def _parse_Arithmetic_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            left = self.parse_Term()
            _ = self.expect("add")
            right = self.parse_Arithmetic()
            res = AdditionNode(left, right)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 1
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            left = self.parse_Term()
            _ = self.expect("subtract")
            right = self.parse_Arithmetic()
            res = SubtractionNode(left, right)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 2
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            term_val = self.parse_Term()
            res = term_val
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for Arithmetic
        found = self.current()
        msg = "No alternative matched for Arithmetic"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = not failed_at_start
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("Arithmetic", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for Arithmetic",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_Arithmetic(self):
        key = ("Arithmetic", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_Arithmetic_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Arithmetic_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    def _parse_Term_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            left = self.parse_Factor()
            _ = self.expect("multiply")
            right = self.parse_Term()
            res = MultiplicationNode(left, right)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 1
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            left = self.parse_Factor()
            _ = self.expect("divide")
            right = self.parse_Term()
            res = DivisionNode(left, right)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 2
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            left = self.parse_Factor()
            _ = self.expect("modulus")
            right = self.parse_Term()
            res = ModulusNode(left, right)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 3
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            term_val = self.parse_Factor()
            res = term_val
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for Term
        found = self.current()
        msg = "No alternative matched for Term"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = not failed_at_start
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("Term", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for Term",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_Term(self):
        key = ("Term", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_Term_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Term_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    def _parse_Factor_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            _ = self.expect("lparen")
            term_val = self.parse_Arithmetic()
            _ = self.expect("rparen")
            res = term_val
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 1
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            term_val = self.parse_Operand()
            res = term_val
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for Factor
        found = self.current()
        msg = "No alternative matched for Factor"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = not failed_at_start
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("Factor", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for Factor",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_Factor(self):
        key = ("Factor", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_Factor_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Factor_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    def _parse_Comparison_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            left = self.parse_Arithmetic()
            _ = self.expect("gte")
            right = self.parse_Arithmetic()
            res = GreaterThanOrEqualNode(left, right)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 1
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            left = self.parse_Arithmetic()
            _ = self.expect("lte")
            right = self.parse_Arithmetic()
            res = LessThanOrEqualNode(left, right)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 2
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            left = self.parse_Arithmetic()
            _ = self.expect("eq")
            right = self.parse_Arithmetic()
            res = EqualNode(left, right)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 3
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            left = self.parse_Arithmetic()
            _ = self.expect("neq")
            right = self.parse_Arithmetic()
            res = NotEqualNode(left, right)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 4
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            left = self.parse_Arithmetic()
            _ = self.expect("gt")
            right = self.parse_Arithmetic()
            res = GreaterThanNode(left, right)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 5
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            left = self.parse_Arithmetic()
            _ = self.expect("lt")
            right = self.parse_Arithmetic()
            res = LessThanNode(left, right)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for Comparison
        found = self.current()
        msg = "No alternative matched for Comparison"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = not failed_at_start
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("Comparison", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for Comparison",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_Comparison(self):
        key = ("Comparison", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_Comparison_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Comparison_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    def _parse_Conditional_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            _ = self.expect("IF_KW")
            cond = self.parse_Expression()
            _ = self.expect("THEN_KW")
            thenBranch = self.parse_Block()
            _ = self.expect("ELIF_KW")
            elifCond = self.parse_Expression()
            _ = self.expect("THEN_KW")
            elifBranch = self.parse_Block()
            _ = self.expect("ELSE_KW")
            elseBranch = self.parse_Block()
            res = ConditionalNode(
                cond, thenBranch, ConditionalNode(elifCond, elifBranch, elseBranch)
            )

            # if-then-else structure
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 1
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            _ = self.expect("IF_KW")
            cond = self.parse_Expression()
            _ = self.expect("THEN_KW")
            thenBranch = self.parse_Block()
            _ = self.expect("ELSE_KW")
            elseBranch = self.parse_Block()
            res = ConditionalNode(cond, thenBranch, elseBranch)

            # if-then structure
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # Option 2
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            _ = self.expect("IF_KW")
            cond = self.parse_Expression()
            _ = self.expect("THEN_KW")
            thenBranch = self.parse_Block()
            res = ConditionalNode(cond, thenBranch, None)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for Conditional
        found = self.current()
        msg = "No alternative matched for Conditional"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = not failed_at_start
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("Conditional", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for Conditional",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_Conditional(self):
        key = ("Conditional", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_Conditional_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Conditional_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    def _parse_Range_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            init = self.parse_Arithmetic()
            _ = self.expect("range_op")
            final = self.parse_Arithmetic()
            res = RangeNode(init, final)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for Range
        found = self.current()
        msg = "No alternative matched for Range"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = not failed_at_start
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("Range", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for Range",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_Range(self):
        key = ("Range", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_Range_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Range_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    def _parse_ForLoop_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        _error_snapshot = len(self.errors)
        try:
            _ = self.expect("FOR_KW")
            var = self.expect("IDENTIFIER")
            _ = self.expect("in_kw")
            range = self.parse_Range()
            _ = self.expect("do_kw")
            body = self.parse_Block()
            res = ForLoopNode(var, range, body)
            if self.enable_recovery and isinstance(res, ErrorNode):
                raise ParseError(res.error_message, token=res.token)
            return res
        except ParseError as e:
            if self.enable_recovery:
                del self.errors[_error_snapshot:]
            failures.append(e)
            pass
        # All alternatives failed for ForLoop
        found = self.current()
        msg = "No alternative matched for ForLoop"
        if failures:
            for f in failures:
                if (
                    not f.message.startswith("Expected ")
                    and not f.message.startswith("No alternative")
                    and not f.message.startswith("Left recursion detected")
                ):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)

        token_at_start = (
            self.tokens[start_pos] if start_pos < len(self.tokens) else None
        )
        failed_at_start = found == token_at_start
        should_recover = not failed_at_start
        if self.enable_recovery and should_recover:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync("ForLoop", start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message="No alternative matched for ForLoop",
                tokens_consumed=self.tokens[start_pos : self.pos],
                token=found,
            )
            return error_node

        raise error

    def parse_ForLoop(self):
        key = ("ForLoop", self.pos)

        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError("Left recursion detected")

            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val

        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos

        try:
            res = self._parse_ForLoop_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e

        if rec.detected:
            if res is None:
                del self.memo[key]
                if "failure_cause" in locals():
                    raise failure_cause
                raise ParseError("Failed after recursion")

            rec.seed = (res, self.pos)
            last_end_pos = self.pos

            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_ForLoop_body()
                    if self.pos > last_end_pos:
                        last_end_pos = self.pos
                        rec.seed = (new_res, self.pos)
                        res = new_res
                    else:
                        break
                except ParseError:
                    break

            self.pos = last_end_pos
            self.memo[key] = (res, self.pos)
            return res

        self.memo[key] = (res, self.pos)
        return res

    @classmethod
    def parse(cls, text, rule_name="Block", enable_recovery=True):
        """Convenience method to parse text directly."""
        # Lexer is expected to be in the same module scope
        lexer = Lexer(text)
        parser = cls(lexer.tokens, enable_recovery=enable_recovery)
        method_name = f"parse_{rule_name}"
        if not hasattr(parser, method_name):
            raise ValueError(f"Unknown rule: {rule_name}")

        try:
            ast = getattr(parser, method_name)()
            if parser.current() is not None:
                found = parser.current()
                msg = f"Expected EOF, found {found.type}"
                parser.add_error(msg, token=found)
        except ParseError as e:
            # If the top-level rule fails and raises ParseError
            parser.errors.append(e)
            ast = None
        except Exception as e:
            # Unexpected errors
            raise e

        return ParseResult(ast, parser.get_errors(), lexer.tokens)
