def generate_common_classes() -> str:
    return """
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

class ParseError(Exception):
    \"\"\"Exception raised when parsing fails.\"\"\"
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
    \"\"\"Result of a parse operation containing the AST and any errors.\"\"\"
    ast: Any
    errors: List[ParseError]
    tokens: List[Token]
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
        
    def unwrap(self):
        \"\"\"Returns the AST if valid, otherwise raises the first error.\"\"\"
        if self.errors:
            raise self.errors[0]
        return self.ast

class ErrorNode:
    \"\"\"Represents an error in the parse tree for recovery mode.\"\"\"
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
"""
