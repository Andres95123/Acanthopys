def generate_common_classes() -> str:
    return """
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
    def __init__(self, message: str, position: int = 0, expected: list = None):
        super().__init__(message)
        self.message = message
        self.position = position
        self.expected = expected or []

class ErrorNode:
    \"\"\"Represents an error in the parse tree for recovery mode.\"\"\"
    def __init__(self, error_message: str = "", tokens_consumed: list = None, 
                 position: int = 0, expected: list = None):
        self.error_message = error_message
        self.tokens_consumed = tokens_consumed or []
        self.position = position
        self.expected = expected or []
    
    def __repr__(self):
        return f'ErrorNode(message={self.error_message!r}, pos={self.position})'
    
    def __str__(self):
        return f'<error at {self.position}: {self.error_message}>'
"""
