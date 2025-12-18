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
    pass
"""
