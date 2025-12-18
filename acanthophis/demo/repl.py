import importlib.util
import os
import sys
import traceback

# Default to the new grammar name
GRAMMAR_NAME = "AdvancedCalc"
GEN_FILE = f"{GRAMMAR_NAME}_parser.py"
GEN_PATH = os.path.join(os.path.dirname(__file__), "generated", GEN_FILE)
MODULE_NAME = "advanced_calc_parser"


def load_parser_module():
    if not os.path.exists(GEN_PATH):
        print(f"\033[91mError: Generated parser not found at {GEN_PATH}\033[0m")
        print(
            "Please run: python acanthophis/main.py demo/calculator.apy -o demo/generated"
        )
        sys.exit(1)

    spec = importlib.util.spec_from_file_location(MODULE_NAME, GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    module = load_parser_module()
    Lexer = getattr(module, "Lexer")
    ParserClass = getattr(module, "Parser")
except Exception as e:
    print(f"\033[91mFailed to load parser module: {e}\033[0m")
    sys.exit(1)


def print_stylized_error(error, source_code):
    if isinstance(error, dict):
        msg = error.get("message")
        line = error.get("line", 0)
        col = error.get("column", 0)
    else:
        msg = getattr(error, "message", str(error))
        line = getattr(error, "line", 0)
        col = getattr(error, "column", 0)

    print(f"\033[91mError:\033[0m {msg}")
    print(f"   --> line {line}:{col}")

    lines = source_code.splitlines()
    if 0 < line <= len(lines):
        code_line = lines[line - 1]
        print(f"{line:4} | {code_line}")
        pointer = " " * (col) + "^"
        print(f"     | \033[93m{pointer}\033[0m")
    print("")


def run_parser(text, recovery=True, verbose=False):
    print(f"\n\033[94mInput:\033[0m {text}")
    try:
        lexer = Lexer(text)
        parser = ParserClass(lexer.tokens, enable_recovery=recovery)

        # Try to parse with the start rule 'Program'
        # The generated parser has methods like parse_Program
        if hasattr(parser, "parse_Program"):
            result = parser.parse_Program()
        elif hasattr(parser, "parse_program"):
            result = parser.parse_program()
        else:
            print(
                "\033[91mError: Could not find start rule (parse_Program) in generated parser.\033[0m"
            )
            return

        if recovery and hasattr(parser, "errors") and parser.errors:
            print(f"\n\033[93mRecovered {len(parser.errors)} Errors:\033[0m")
            for e in parser.errors:
                print_stylized_error(e, text)
            print("\033[90mPartial AST:\033[0m", result)
        else:
            print("\033[92mSuccess!\033[0m")
            print("AST:", result)

    except Exception as e:
        print("\033[91mParse Error (Immediate Failure):\033[0m")
        print_stylized_error(e, text)
        if verbose:
            traceback.print_exc()


def run_examples():
    examples = [
        ("1. Basic Arithmetic (Precedence)", "let x = 1 + 2 * 3;"),
        ("2. Left Associativity (Left Recursion)", "let y = 10 - 5 - 2;"),
        ("3. Complex Expression", "print((1 + 2) * (3 + 4));"),
        ("4. Comparisons", "if 1 + 1 == 2 { print(1); }"),
        ("5. Error Recovery (Missing Semicolon)", "let x = 10 print(x);"),
        ("6. Error Recovery (Unexpected Token)", "let x = 10 + * 5;"),
    ]

    print(f"\n\033[1mRunning {len(examples)} internal test cases...\033[0m")
    for title, code in examples:
        print(f"\n\033[1m=== {title} ===\033[0m")
        run_parser(code, recovery=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "examples":
        run_examples()
        sys.exit(0)

    print(f"\033[1mAcanthophis REPL ({GRAMMAR_NAME})\033[0m")
    print("Type 'exit' to quit, 'examples' to run demo cases.")

    while True:
        try:
            text = input("\033[96m>\033[0m ")
        except EOFError:
            break

        if not text.strip():
            continue

        if text.strip().lower() in {"exit", "quit"}:
            break

        if text.strip().lower() == "examples":
            run_examples()
            continue

        run_parser(text, recovery=True)

        run_parser(text, recovery=False)
        run_parser(text, recovery=True)
        print("-" * 40)
