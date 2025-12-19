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
    def __init__(self, error_message: str = "", token=None, tokens_consumed: list = None, 
                 expected: list = None):
        self.error_message = error_message
        self.token = token
        self.tokens_consumed = tokens_consumed or []
        self.expected = expected or []
        self.line = token.line if token else 0
        self.column = token.column if token else 0
    
    def __repr__(self):
        return f'ErrorNode(message={self.error_message!r}, line={self.line}, col={self.column})'
    
    def __str__(self):
        return f'<error at {self.line}:{self.column}: {self.error_message}>'

class LeftRecursion:
    def __init__(self):
        self.detected = False
        self.seed = None

class Add:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != 'args':
                params.append(repr(v))
        return f'Add({', '.join(params)})'

class Div:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != 'args':
                params.append(repr(v))
        return f'Div({', '.join(params)})'

class Mul:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != 'args':
                params.append(repr(v))
        return f'Mul({', '.join(params)})'

class Num:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != 'args':
                params.append(repr(v))
        return f'Num({', '.join(params)})'

class Sub:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != 'args':
                params.append(repr(v))
        return f'Sub({', '.join(params)})'

class Var:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != 'args':
                params.append(repr(v))
        return f'Var({', '.join(params)})'

class expr:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        params = []
        if self.args:
            params.extend([repr(a) for a in self.args])
        for k, v in self.__dict__.items():
            if k != 'args':
                params.append(repr(v))
        return f'expr({', '.join(params)})'

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.tokens = []
        self.tokenize()

    def tokenize(self):
        # Regex patterns
        token_specs = [
            ('TOKEN_NUMBER', r'\d+'),
            ('TOKEN_PLUS', r'\+'),
            ('TOKEN_MULU', r'\*'),
            ('TOKEN_DIV', r'\/'),
            ('TOKEN_MINUS', r'-'),
            ('TOKEN_WS', r'\s+'),
            ('TOKEN_OPENB', r'"("'),
            ('TOKEN_CLOSEB', r'")"'),
            ('TOKEN_IDENTIFIER', r'[a-zA-Z_]\w*'),
            ('MISMATCH', r'.'),
        ]

        group_map = {'TOKEN_NUMBER': 'NUMBER', 'TOKEN_PLUS': 'PLUS', 'TOKEN_MULU': 'MULU', 'TOKEN_DIV': 'DIV', 'TOKEN_MINUS': 'MINUS', 'TOKEN_WS': 'WS', 'TOKEN_OPENB': 'OPENB', 'TOKEN_CLOSEB': 'CLOSEB', 'TOKEN_IDENTIFIER': 'IDENTIFIER'}

        # Compile regex
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specs)
        get_token = re.compile(tok_regex).match

        skipped_tokens = {'WS'}
        line_num = 1
        line_start = 0
        mo = get_token(self.text)
        while mo is not None:
            kind = mo.lastgroup
            value = mo.group(kind)
            if kind == 'MISMATCH':
                raise ParseError(f'Unexpected character {value!r} on line {line_num}')
            
            # Map back to token type
            token_type = group_map.get(kind, kind)
            
            if token_type in skipped_tokens:
                pass
            else:
                self.tokens.append(Token(token_type, value, line_num, mo.start() - line_start))
            
            # Update position
            pos = mo.end()
            mo = get_token(self.text, pos)
            if pos == len(self.text): break

class Parser:
    def __init__(self, tokens, enable_recovery=False):
        self.tokens = tokens
        self.pos = 0
        self.memo = {}
        self.enable_recovery = enable_recovery
        self.errors = []
        # Synchronization tokens for each rule (computed during generation)
        self.sync_tokens = {
            'Expr': ['CLOSEB', 'EOF', 'IDENTIFIER', 'MINUS', 'NUMBER', 'OPENB', 'PLUS'],
            'Term': ['CLOSEB', 'DIV', 'EOF', 'IDENTIFIER', 'MINUS', 'MULU', 'NUMBER', 'OPENB', 'PLUS'],
            'Byte': ['CLOSEB', 'DIV', 'EOF', 'IDENTIFIER', 'MINUS', 'MULU', 'NUMBER', 'OPENB', 'PLUS'],
            'Factor': ['CLOSEB', 'DIV', 'EOF', 'IDENTIFIER', 'MINUS', 'MULU', 'NUMBER', 'OPENB', 'PLUS'],
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
            msg = f'Expected {type_name}, found {found.type if found else "EOF"}'
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
        self.errors.append({
            'message': error_msg,
            'token': token,
            'expected': expected or [],
            'line': token.line if token else 0,
            'column': token.column if token else 0,
        })

    def get_errors(self):
        """Get all recorded errors."""
        return self.errors.copy()

    def error(self, msg):
        raise ParseError(msg, token=self.current())

    def _parse_Expr_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        try:
            left = self.parse_Expr()
            _ = self.expect('PLUS')
            right = self.parse_Term()
            res = Add(left, right)
            return res
        except ParseError as e:
            failures.append(e)
            pass
        # Option 1
        self.pos = start_pos
        try:
            left = self.parse_Expr()
            _ = self.expect('MINUS')
            right = self.parse_Term()
            res = Sub(left, right)
            return res
        except ParseError as e:
            failures.append(e)
            pass
        # Option 2
        self.pos = start_pos
        try:
            val = self.parse_Term()
            res = val
            return res
        except ParseError as e:
            failures.append(e)
            pass
        # All alternatives failed for Expr
        found = self.current()
        msg = 'No alternative matched for Expr'
        if failures:
            for f in failures:
                if not f.message.startswith('Expected ') and not f.message.startswith('No alternative') and not f.message.startswith('Left recursion detected'):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)
        
        if self.enable_recovery:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync('Expr', start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message='No alternative matched for Expr',
                tokens_consumed=self.tokens[start_pos:self.pos],
                token=found
            )
            return error_node
        
        raise error

    def parse_Expr(self):
        key = ('Expr', self.pos)
        
        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError('Left recursion detected')
            
            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val
        
        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos
        
        try:
            res = self._parse_Expr_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e
        
        if rec.detected:
            if res is None:
                del self.memo[key]
                if 'failure_cause' in locals():
                    raise failure_cause
                raise ParseError('Failed after recursion')
            
            rec.seed = (res, self.pos)
            last_end_pos = self.pos
            
            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Expr_body()
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
        try:
            left = self.parse_Term()
            _ = self.expect('MULU')
            right = self.parse_Factor()
            res = Mul(left, right)
            return res
        except ParseError as e:
            failures.append(e)
            pass
        # Option 1
        self.pos = start_pos
        try:
            left = self.parse_Term()
            _ = self.expect('DIV')
            right = self.parse_Factor()
            res = Div(left, right)
            return res
        except ParseError as e:
            failures.append(e)
            pass
        # Option 2
        self.pos = start_pos
        try:
            val = self.parse_Factor()
            res = val
            return res
        except ParseError as e:
            failures.append(e)
            pass
        # All alternatives failed for Term
        found = self.current()
        msg = 'No alternative matched for Term'
        if failures:
            for f in failures:
                if not f.message.startswith('Expected ') and not f.message.startswith('No alternative') and not f.message.startswith('Left recursion detected'):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)
        
        if self.enable_recovery:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync('Term', start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message='No alternative matched for Term',
                tokens_consumed=self.tokens[start_pos:self.pos],
                token=found
            )
            return error_node
        
        raise error

    def parse_Term(self):
        key = ('Term', self.pos)
        
        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError('Left recursion detected')
            
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
                if 'failure_cause' in locals():
                    raise failure_cause
                raise ParseError('Failed after recursion')
            
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

    def _parse_Byte_body(self):
        start_pos = self.pos
        error = self.error
        failures = []
        # Option 0
        self.pos = start_pos
        try:
            n = self.expect('NUMBER')
            res = int(n)
            # Check Guard
            if int(n) < 256:
                pass
            else:
                error("Byte value out of range")
            return res
        except ParseError as e:
            failures.append(e)
            pass
        # All alternatives failed for Byte
        found = self.current()
        msg = 'No alternative matched for Byte'
        if failures:
            for f in failures:
                if not f.message.startswith('Expected ') and not f.message.startswith('No alternative') and not f.message.startswith('Left recursion detected'):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)
        
        if self.enable_recovery:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync('Byte', start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message='No alternative matched for Byte',
                tokens_consumed=self.tokens[start_pos:self.pos],
                token=found
            )
            return error_node
        
        raise error

    def parse_Byte(self):
        key = ('Byte', self.pos)
        
        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError('Left recursion detected')
            
            val, end_pos = res
            if isinstance(val, Exception):
                raise val
            self.pos = end_pos
            return val
        
        rec = LeftRecursion()
        self.memo[key] = rec
        start_pos = self.pos
        
        try:
            res = self._parse_Byte_body()
        except ParseError as e:
            if not rec.detected:
                self.memo[key] = (e, start_pos)
                raise e
            res = None
            failure_cause = e
        
        if rec.detected:
            if res is None:
                del self.memo[key]
                if 'failure_cause' in locals():
                    raise failure_cause
                raise ParseError('Failed after recursion')
            
            rec.seed = (res, self.pos)
            last_end_pos = self.pos
            
            while True:
                self.pos = start_pos
                try:
                    new_res = self._parse_Byte_body()
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
        try:
            _ = self.expect('OPENB')
            expr = self.parse_Expr()
            _ = self.expect('CLOSEB')
            res = expr
            return res
        except ParseError as e:
            failures.append(e)
            pass
        # Option 1
        self.pos = start_pos
        try:
            n = self.parse_Byte()
            res = Num(n)
            return res
        except ParseError as e:
            failures.append(e)
            pass
        # Option 2
        self.pos = start_pos
        try:
            id = self.expect('IDENTIFIER')
            res = Var(id)
            return res
        except ParseError as e:
            failures.append(e)
            pass
        # All alternatives failed for Factor
        found = self.current()
        msg = 'No alternative matched for Factor'
        if failures:
            for f in failures:
                if not f.message.startswith('Expected ') and not f.message.startswith('No alternative') and not f.message.startswith('Left recursion detected'):
                    msg = f.message
                    found = f.token
                    break
        error = ParseError(msg, token=found)
        
        if self.enable_recovery:
            if found is None:
                raise error
            self.add_error(error.message, token=found)
            self.skip_to_sync('Factor', start_pos)
            # Return ErrorNode for recovery mode
            error_node = ErrorNode(
                error_message='No alternative matched for Factor',
                tokens_consumed=self.tokens[start_pos:self.pos],
                token=found
            )
            return error_node
        
        raise error

    def parse_Factor(self):
        key = ('Factor', self.pos)
        
        if key in self.memo:
            res = self.memo[key]
            if isinstance(res, LeftRecursion):
                res.detected = True
                if res.seed is not None:
                    val, end_pos = res.seed
                    self.pos = end_pos
                    return val
                else:
                    raise ParseError('Left recursion detected')
            
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
                if 'failure_cause' in locals():
                    raise failure_cause
                raise ParseError('Failed after recursion')
            
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

    @classmethod
    def parse(cls, text, rule_name='Expr', enable_recovery=True):
        """Convenience method to parse text directly."""
        # Lexer is expected to be in the same module scope
        lexer = Lexer(text)
        parser = cls(lexer.tokens, enable_recovery=enable_recovery)
        method_name = f'parse_{rule_name}'
        if not hasattr(parser, method_name):
            raise ValueError(f'Unknown rule: {rule_name}')
        
        try:
            ast = getattr(parser, method_name)()
            if parser.current() is not None:
                found = parser.current()
                msg = f'Expected EOF, found {found.type}'
                parser.add_error(msg, token=found)
        except ParseError as e:
            # If the top-level rule fails and raises ParseError
            parser.errors.append(e)
            ast = None
        except Exception as e:
            # Unexpected errors
            raise e
            
        return ParseResult(ast, parser.get_errors(), lexer.tokens)