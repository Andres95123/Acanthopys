import sys
import traceback
from parser import Parser
from utils.generators import CodeGenerator
from cli.console import Colors, print_error, print_info, print_success, print_warning


import sys
import traceback
import os
import time
from parser import Parser
from utils.generators import CodeGenerator
from cli.console import Colors, print_error, print_info, print_success, print_warning


def run_repl(grammar_path: str, start_rule: str = None, watch: bool = True):
    """
    Runs an interactive REPL for the given grammar file.
    """
    print_info(f"Starting REPL for {grammar_path}...")

    if not os.path.exists(grammar_path):
        print_error(f"File not found: {grammar_path}")
        return 1

    def load_parser():
        try:
            with open(grammar_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print_error(f"Failed to read file: {e}")
            return None, None

        # 1. Parse Grammar
        parser = Parser()
        try:
            grammars = parser.parse(content)
        except Exception as e:
            print_error(f"Failed to parse grammar: {e}")
            return None, None

        if not grammars:
            print_error("No grammar found in file.")
            return None, None

        grammar = grammars[0]  # Use the first grammar

        # 2. Generate Code
        try:
            generator = CodeGenerator(grammar, enable_recovery=True)
            code = generator.generate()
        except Exception as e:
            print_error(f"Failed to generate parser: {e}")
            return None, None

        # 3. Load Module
        namespace = {}
        try:
            exec(code, namespace)
        except Exception as e:
            print_error(f"Failed to execute generated code: {e}")
            traceback.print_exc()
            return None, None

        ParserClass = namespace.get("Parser")

        if not ParserClass:
            print_error("Generated code does not contain Parser class.")
            return None, None

        # Determine start rule
        current_rule_name = start_rule
        if not current_rule_name:
            start_rules = [r for r in grammar.rules if r.is_start]
            if start_rules:
                current_rule_name = start_rules[0].name
            elif grammar.rules:
                current_rule_name = grammar.rules[0].name
            else:
                print_error("Grammar has no rules.")
                return None, None

        return ParserClass, current_rule_name, grammar.name

    # Initial Load
    loaded = load_parser()
    if not loaded or not loaded[0]:
        return 1

    ParserClass, rule_name, grammar_name = loaded
    print_success(f"Loaded grammar: {grammar_name}")
    print_info(f"Using start rule: {Colors.BOLD}{rule_name}{Colors.RESET}")
    print(f"{Colors.DIM}Type 'exit' or 'quit' to leave.{Colors.RESET}\n")

    last_mtime = os.path.getmtime(grammar_path)

    # 4. REPL Loop
    while True:
        # Check for updates before input (lazy watch)
        if watch:
            try:
                current_mtime = os.path.getmtime(grammar_path)
                if current_mtime != last_mtime:
                    last_mtime = current_mtime
                    print(f"\n{Colors.YELLOW}File changed. Reloading...{Colors.RESET}")
                    new_loaded = load_parser()
                    if new_loaded and new_loaded[0]:
                        ParserClass, rule_name, grammar_name = new_loaded
                        print_success(f"Reloaded {grammar_name} successfully.")
                    else:
                        print_error("Reload failed. Keeping previous version.")
                    print(f"{Colors.GREEN}>>> {Colors.RESET}", end="", flush=True)
            except OSError:
                pass

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
                else:
                    print(f"{Colors.CYAN}{result.ast}{Colors.RESET}")

            except Exception as e:
                print(f"{Colors.RED}Runtime Error: {e}{Colors.RESET}")
                # traceback.print_exc()

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            break

    return 0
