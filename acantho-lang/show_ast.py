import sys
import os
import json

# Add current directory to path to allow imports from vendor
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from vendor.acanthophis.parser import Parser
except ImportError:
    # Fallback for when running in a different context or if utils is not found
    print(
        "Error: Could not import vendor.acanthophis.parser. Make sure the vendor folder exists."
    )
    sys.exit(1)


def serialize(obj):
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    if hasattr(obj, "__dict__"):
        return {k: serialize(v) for k, v in obj.__dict__.items()}
    return obj


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python show_ast.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        parser = Parser()
        grammars = parser.parse(content)

        # Serialize and print
        print(json.dumps(serialize(grammars), indent=2))

    except Exception as e:
        print(f"Error parsing file: {e}")
        sys.exit(1)
