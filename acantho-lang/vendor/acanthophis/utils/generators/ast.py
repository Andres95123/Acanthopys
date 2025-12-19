from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parser import Grammar


BUILTINS = {"int", "float", "str", "bool", "list", "dict", "tuple", "set", "None"}


def generate_ast_nodes(grammar: "Grammar") -> str:
    # Collect all node names from rules
    node_names = set()
    for rule in grammar.rules:
        for expr in rule.expressions:
            ret = expr.return_object
            if ret == "pass":
                continue
            # Check if it's a call like NumberNode(float(value))
            if "(" in ret:
                name = ret.split("(")[0]
                if name not in BUILTINS:
                    node_names.add(name)
            else:
                if ret not in BUILTINS:
                    node_names.add(ret)

    lines = []
    for name in sorted(node_names):
        lines.append(f"class {name}:")
        lines.append(f"    def __init__(self, *args, **kwargs):")
        lines.append(f"        self.args = args")
        lines.append(f"        for k, v in kwargs.items():")
        lines.append(f"            setattr(self, k, v)")
        lines.append(f"    def __repr__(self):")
        lines.append(f"        params = []")
        lines.append(f"        if self.args:")
        lines.append(f"            params.extend([repr(a) for a in self.args])")
        lines.append(f"        for k, v in self.__dict__.items():")
        lines.append(f"            if k != 'args':")
        lines.append(f"                params.append(repr(v))")
        lines.append(f"        return f'{name}({{', '.join(params)}})'")
        lines.append("")

    return "\n".join(lines)
