import re
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from parser import Grammar


def generate_lexer(grammar: "Grammar", literal_map: Dict[str, str]) -> str:
    lines = []
    lines.append("class Lexer:")
    lines.append("    def __init__(self, text):")
    lines.append("        self.text = text")
    lines.append("        self.pos = 0")
    lines.append("        self.tokens = []")
    lines.append("        self.tokenize()")
    lines.append("")
    lines.append("    def tokenize(self):")
    lines.append("        # Regex patterns")

    lines.append("        token_specs = [")

    # We need to map group names to token types because group names must be identifiers
    group_map = {}

    for token in grammar.tokens:
        group_name = f"TOKEN_{token.name}"
        group_map[group_name] = token.name
        lines.append(f"            ('{group_name}', r'{token.pattern}'),")

    # Add literals
    for lit, group_name in literal_map.items():
        # Escape regex special chars in literal
        escaped = re.escape(lit)
        group_map[group_name] = (
            lit  # Use literal value as token type? Or the group name?
        )
        # If we use literal value as token type, then expect('(') works.
        # But expect('TOKEN_plus') works for tokens.
        # Let's use the literal value as the token type for literals.
        lines.append(f"            ('{group_name}', r'{escaped}'),")

    lines.append("            ('MISMATCH', r'.'),")
    lines.append("        ]")
    lines.append("")
    lines.append(f"        group_map = {group_map}")
    lines.append("")
    lines.append("        # Compile regex")
    lines.append(
        "        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specs)"
    )
    lines.append("        get_token = re.compile(tok_regex).match")
    lines.append("")

    # Identify skipped tokens
    skipped_tokens = [t.name for t in grammar.tokens if t.skip]
    lines.append(f"        skipped_tokens = {repr(set(skipped_tokens))}")

    lines.append("        line_num = 1")
    lines.append("        line_start = 0")
    lines.append("        mo = get_token(self.text)")
    lines.append("        while mo is not None:")
    lines.append("            kind = mo.lastgroup")
    lines.append("            value = mo.group(kind)")
    lines.append("            if kind == 'MISMATCH':")
    lines.append(
        "                raise ParseError(f'Unexpected character {value!r} on line {line_num}')"
    )
    lines.append("            ")
    lines.append("            # Map back to token type")
    lines.append("            token_type = group_map.get(kind, kind)")
    lines.append("            ")
    lines.append("            if token_type in skipped_tokens:")
    lines.append("                pass")
    lines.append("            else:")
    lines.append(
        "                self.tokens.append(Token(token_type, value, line_num, mo.start() - line_start))"
    )
    lines.append("            ")
    lines.append("            # Update position")
    lines.append("            pos = mo.end()")
    lines.append("            mo = get_token(self.text, pos)")
    lines.append("            if pos == len(self.text): break")
    lines.append("")

    return "\n".join(lines)
