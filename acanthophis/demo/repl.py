import importlib.util
import os
import sys
import traceback
import glob
import subprocess
import time
import argparse

# Add project root to path
# Go up two levels: demo -> acanthophis -> root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from acanthophis.parser import Parser as GrammarParser

# Constants
DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
GRAMMARS_DIR = os.path.join(DEMO_DIR, "grammars")
GENERATED_DIR = os.path.join(DEMO_DIR, "generated")

# Ensure generated dir exists
os.makedirs(GENERATED_DIR, exist_ok=True)


class REPL:
    def __init__(self):
        self.grammar_file = None
        self.grammar_name = None
        self.parser_module = None
        self.Lexer = None
        self.ParserClass = None
        self.verbose = False
        self.show_ast = True
        self.show_tokens = False
        self.enable_recovery = True

    def list_grammars(self):
        files = glob.glob(os.path.join(GRAMMARS_DIR, "*.apy"))
        return [os.path.basename(f) for f in files]

    def select_grammar(self):
        grammars = self.list_grammars()
        if not grammars:
            print("\033[91mNo grammars found in demo/grammars/\033[0m")
            sys.exit(1)

        print("\n\033[1mAvailable Grammars:\033[0m")
        for i, g in enumerate(grammars):
            print(f"  \033[96m{i + 1}.\033[0m {g}")

        while True:
            try:
                choice = input("\nSelect a grammar (number): ").strip()
                if not choice:
                    continue
                idx = int(choice) - 1
                if 0 <= idx < len(grammars):
                    self.grammar_file = os.path.join(GRAMMARS_DIR, grammars[idx])
                    print(f"Selected: \033[92m{grammars[idx]}\033[0m")
                    break
                else:
                    print("Invalid number.")
            except ValueError:
                print("Please enter a number.")
            except KeyboardInterrupt:
                sys.exit(0)

    def compile_grammar(self):
        print(f"\033[90mCompiling {os.path.basename(self.grammar_file)}...\033[0m")

        # Use subprocess to run the CLI to ensure clean state and proper file generation
        cmd = [
            sys.executable,
            os.path.join(DEMO_DIR, "..", "main.py"),
            self.grammar_file,
            "-o",
            GENERATED_DIR,
        ]

        if self.verbose:
            cmd.append("-v")

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", env=env
        )

        if result.returncode != 0:
            print("\033[91mCompilation Failed:\033[0m")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

        # Extract grammar name from file content to know the generated file name
        # Or parse the output? The CLI outputs "Generating parser for grammar: NAME"
        # But simpler is to parse the grammar file quickly here to get the name.
        try:
            with open(self.grammar_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Quick regex or use the actual parser
            gp = GrammarParser()
            grammars = gp.parse(content)
            if not grammars:
                print("\033[91mNo grammar found in file.\033[0m")
                return False

            self.grammar_name = grammars[0].name
            return True
        except Exception as e:
            print(f"\033[91mError parsing grammar definition: {e}\033[0m")
            return False

    def load_module(self):
        if not self.grammar_name:
            return False

        module_name = f"{self.grammar_name}_parser"
        file_path = os.path.join(GENERATED_DIR, f"{module_name}.py")

        if not os.path.exists(file_path):
            print(f"\033[91mGenerated file not found: {file_path}\033[0m")
            return False

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            self.parser_module = module
            self.Lexer = getattr(module, "Lexer")
            self.ParserClass = getattr(module, "Parser")
            return True
        except Exception as e:
            print(f"\033[91mFailed to load module: {e}\033[0m")
            traceback.print_exc()
            return False

    def print_error(self, error, source_code):
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

    def run_input(self, text):
        if not self.Lexer or not self.ParserClass:
            print("Parser not loaded.")
            return

        if self.show_tokens:
            print("\033[90mTokens:\033[0m")
            try:
                l = self.Lexer(text)
                for t in l.tokens:
                    print(f"  {t}")
            except Exception as e:
                print(f"  Tokenization Error: {e}")

        try:
            lexer = self.Lexer(text)
            parser = self.ParserClass(
                lexer.tokens, enable_recovery=self.enable_recovery
            )

            # Find start rule
            # Heuristic: try 'parse_start_rule_name' if we knew it,
            # but we can inspect the class methods.
            # Or just try common names or the first parse_ method found.

            method_name = None
            # Try to find the start rule from the grammar definition if we parsed it earlier
            # But we don't have the grammar object handy here easily without re-parsing.
            # Let's inspect the parser class.

            methods = [
                func
                for func in dir(parser)
                if callable(getattr(parser, func)) and func.startswith("parse_")
            ]
            # Filter out internal methods like _parse_...
            methods = [m for m in methods if not m.startswith("parse__")]

            if not methods:
                print("\033[91mNo parse methods found in generated parser.\033[0m")
                return

            # Prefer 'parse_program', 'parse_start', 'parse_expr' or the first one
            preferred = ["parse_program", "parse_Program", "parse_start", "parse_expr"]
            for p in preferred:
                if p in methods:
                    method_name = p
                    break

            if not method_name:
                method_name = methods[0]  # Default to first found

            if self.verbose:
                print(f"\033[90mUsing start rule: {method_name}\033[0m")

            parse_method = getattr(parser, method_name)
            result = parse_method()

            if self.enable_recovery and hasattr(parser, "errors") and parser.errors:
                print(f"\n\033[93mRecovered {len(parser.errors)} Errors:\033[0m")
                for e in parser.errors:
                    self.print_error(e, text)
                if self.show_ast:
                    print("\033[90mPartial AST:\033[0m", result)
            else:
                print("\033[92mSuccess!\033[0m")
                if self.show_ast:
                    print("AST:", result)

        except Exception as e:
            print("\033[91mParse Error (Immediate Failure):\033[0m")
            self.print_error(e, text)
            if self.verbose:
                traceback.print_exc()

    def run_tests(self):
        print(
            f"\033[90mRunning integrated tests for {os.path.basename(self.grammar_file)}...\033[0m"
        )
        cmd = [
            sys.executable,
            os.path.join(DEMO_DIR, "..", "main.py"),
            self.grammar_file,
            "--tests",
        ]
        subprocess.run(cmd)

    def print_help(self):
        print("\n\033[1mCommands:\033[0m")
        print("  \033[96m:reload\033[0m   Recompile and reload the current grammar")
        print("  \033[96m:change\033[0m   Select a different grammar")
        print("  \033[96m:test\033[0m     Run integrated tests defined in the grammar")
        print("  \033[96m:debug\033[0m    Toggle verbose debug mode")
        print("  \033[96m:ast\033[0m      Toggle AST printing")
        print("  \033[96m:tokens\033[0m   Toggle token printing")
        print("  \033[96m:rec\033[0m      Toggle error recovery")
        print("  \033[96m:cls\033[0m      Clear screen")
        print("  \033[96m:help\033[0m     Show this help")
        print("  \033[96mexit\033[0m      Quit REPL")

    def start(self):
        print(f"\033[1mAcanthophis REPL v2.0\033[0m")

        # Initial selection
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.grammar_file = sys.argv[1]
        else:
            self.select_grammar()

        # Initial compile & load
        if self.compile_grammar():
            self.load_module()

        print(
            f"\nLoaded \033[92m{self.grammar_name}\033[0m. Type ':help' for commands."
        )

        while True:
            try:
                prompt = f"\033[96m{self.grammar_name}>\033[0m "
                text = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            if not text:
                continue

            if text.startswith(":"):
                cmd = text[1:].lower()
                if cmd == "reload":
                    if self.compile_grammar():
                        self.load_module()
                        print("Reloaded.")
                elif cmd == "change":
                    self.select_grammar()
                    if self.compile_grammar():
                        self.load_module()
                elif cmd == "test":
                    self.run_tests()
                elif cmd == "debug":
                    self.verbose = not self.verbose
                    print(f"Verbose mode: {self.verbose}")
                elif cmd == "ast":
                    self.show_ast = not self.show_ast
                    print(f"Show AST: {self.show_ast}")
                elif cmd == "tokens":
                    self.show_tokens = not self.show_tokens
                    print(f"Show Tokens: {self.show_tokens}")
                elif cmd == "rec":
                    self.enable_recovery = not self.enable_recovery
                    print(f"Error Recovery: {self.enable_recovery}")
                elif cmd == "cls":
                    os.system("cls" if os.name == "nt" else "clear")
                elif cmd == "help":
                    self.print_help()
                else:
                    print(f"Unknown command: {cmd}")
                continue

            if text.lower() in {"exit", "quit"}:
                break

            self.run_input(text)


if __name__ == "__main__":
    repl = REPL()
    repl.start()
