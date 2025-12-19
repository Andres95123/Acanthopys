import sys
import traceback
from parser import Parser
from utils.generators import CodeGenerator
from cli.console import Colors, print_error, print_info, print_success, print_warning


def run_repl(grammar_path: str, start_rule: str = None):
    """
    Runs an interactive REPL for the given grammar file.
    """
    print_info(f"Starting REPL for {grammar_path}...")

    try:
        with open(grammar_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print_error(f"File not found: {grammar_path}")
        return 1

    # 1. Parse Grammar
    parser = Parser()
    try:
        grammars = parser.parse(content)
    except Exception as e:
        print_error(f"Failed to parse grammar: {e}")
        return 1

    if not grammars:
        print_error("No grammar found in file.")
        return 1

    grammar = grammars[0]  # Use the first grammar
    print_success(f"Loaded grammar: {grammar.name}")

    # 2. Generate Code
    try:
        generator = CodeGenerator(grammar, enable_recovery=True)
        code = generator.generate()
    except Exception as e:
        print_error(f"Failed to generate parser: {e}")
        return 1

    # 3. Load Module
    namespace = {}
    try:
        exec(code, namespace)
    except Exception as e:
        print_error(f"Failed to execute generated code: {e}")
        traceback.print_exc()
        return 1

    ParserClass = namespace.get("Parser")

    if not ParserClass:
        print_error("Generated code does not contain Parser class.")
        return 1

    # Determine start rule
    if start_rule:
        rule_name = start_rule
    else:
        start_rules = [r for r in grammar.rules if r.is_start]
        if start_rules:
            rule_name = start_rules[0].name
        elif grammar.rules:
            rule_name = grammar.rules[0].name
        else:
            print_error("Grammar has no rules.")
            return 1

    print_info(f"Using start rule: {Colors.BOLD}{rule_name}{Colors.RESET}")
    print(f"{Colors.DIM}Type 'exit' or 'quit' to leave.{Colors.RESET}\n")

    # 4. REPL Loop
    while True:
        try:
            text = input(f"{Colors.GREEN}>>> {Colors.RESET}")
            if text.lower() in ("exit", "quit"):
                break
            if not text.strip():
                continue

            try:
                # Use the new static parse method
                result = ParserClass.parse(
                    text, rule_name=rule_name, enable_recovery=True
                )

                if result.errors:
                    print(f"\n{Colors.RED}{Colors.BOLD}Errors found:{Colors.RESET}")
                    for err in result.errors:
                        # Assuming err is a ParseError or dict-like from recovery
                        if isinstance(err, dict):
                            msg = err.get("message", "Unknown error")
                            line = err.get("line", "?")
                            col = err.get("column", "?")
                            print(
                                f"  {Colors.RED}✖ {msg} at line {line}, col {col}{Colors.RESET}"
                            )
                        else:
                            print(f"  {Colors.RED}✖ {err}{Colors.RESET}")

                    if result.ast:
                        print(f"\n{Colors.YELLOW}Partial AST generated:{Colors.RESET}")
                        print(f"{Colors.DIM}{result.ast}{Colors.RESET}")
                else:
                    print(f"{Colors.CYAN}{result.ast}{Colors.RESET}")

            except Exception as e:
                print(f"{Colors.RED}Runtime Error: {e}{Colors.RESET}")
                traceback.print_exc()

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            break

    return 0
