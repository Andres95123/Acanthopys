import os
import sys
import time
import json
from parser import Parser
from utils.logging import Logger
from testing.runner import run_tests_in_memory
from utils.generators import CodeGenerator
from linter.venom_linter import VenomLinter
from formatter.constrictor_formatter import ConstrictorFormatter
from cli.console import Colors, print_success, print_error, print_info, print_warning


def run_init(name: str, output_dir: str = ".") -> int:
    """Initialize a new grammar file."""
    filename = f"{name}.apy"
    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath):
        print_error(f"File '{filepath}' already exists.")
        return 1

    template = f"""grammar {name}:
    tokens:
        NUMBER: \\d+
        PLUS: \\+
        MINUS: -
        WS: skip \\s+
    end

    start rule Expr:
        | left:Expr PLUS right:Term -> Add(left, right)
        | left:Expr MINUS right:Term -> Sub(left, right)
        | val:Term -> pass
    end

    rule Term:
        | n:NUMBER -> Num(int(n))
    end

    test Basic:
        "1 + 2" => Yields(Add(Num(1), Num(2)))
    end
end
"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(template)
        print_success(f"Created new grammar project: {filepath}")
        return 0
    except Exception as e:
        print_error(f"Failed to create file: {e}")
        return 1


def run_build(
    input_path: str,
    output_dir: str = ".",
    no_tests: bool = False,
    dry_run: bool = False,
    enable_recovery: bool = True,
    verbose: bool = False,
    watch: bool = False,
) -> int:
    """Build/Generate the parser."""

    def build_step(path, **kwargs):
        logger = Logger(use_color=True, verbose=verbose)
        start_time = time.perf_counter()

        if not os.path.exists(path):
            logger.error(f"Input file not found: {path}")
            return 1

        logger.info(f"Building parser from {path}...")

        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            acantho_parser = Parser()
            grammars = acantho_parser.parse(content)

            if not grammars:
                logger.warn("No grammars found in file.")
                return 0

            for grammar in grammars:
                logger.info(f"Compiling grammar: {grammar.name}")

                generator = CodeGenerator(grammar, enable_recovery=enable_recovery)
                code = generator.generate()

                if grammar.tests and not no_tests:
                    logger.info(f"Running tests for: {grammar.name}")
                    success = run_tests_in_memory(grammar, code, logger)
                    if not success:
                        logger.error(f"Tests failed for grammar: {grammar.name}")
                        return 1
                    print_success("Tests passed!")

                if not dry_run:
                    output_filename = f"{grammar.name}_parser.py"
                    output_path_full = os.path.join(output_dir, output_filename)
                    os.makedirs(output_dir, exist_ok=True)

                    with open(output_path_full, "w", encoding="utf-8") as f:
                        f.write(code)
                    print_success(f"Generated {output_path_full}")
                else:
                    logger.info("Dry run: No files written.")

            duration = time.perf_counter() - start_time
            print_info(f"Finished in {duration:.4f}s.")
            return 0

        except Exception as e:
            logger.error(f"Build failed: {e}")
            if verbose:
                import traceback

                traceback.print_exc()
            return 1

    if watch:
        print_info(f"Watching {input_path} for changes...")
        try:
            # Initial build
            build_step(input_path)

            last_mtime = os.path.getmtime(input_path)
            while True:
                time.sleep(0.5)
                try:
                    current_mtime = os.path.getmtime(input_path)
                    if current_mtime != last_mtime:
                        last_mtime = current_mtime
                        print("\n" + "-" * 40)
                        print_info(f"File changed. Rebuilding...")
                        build_step(input_path)
                except OSError:
                    pass
        except KeyboardInterrupt:
            print_info("Stopping watch mode.")
            return 0
    else:
        return build_step(input_path)


def run_check(input_path: str, json_output: bool = False) -> int:
    """Lint/Check the grammar."""
    try:
        linter = VenomLinter(input_path)
        results = linter.lint()

        has_error = any(d["severity"] == "Error" for d in results)

        if json_output:
            print(json.dumps(results, indent=2))
        else:
            if not results:
                print_success("No issues found.")
            else:
                for diag in results:
                    color = Colors.RED if diag["severity"] == "Error" else Colors.YELLOW
                    print(
                        f"{color}{diag['severity']}{Colors.RESET} in {diag['file']}:{diag['line']} - {diag['message']}"
                    )

                if has_error:
                    print_error("Check failed with errors.")
                else:
                    print_success("Check passed with warnings.")

        return 1 if has_error else 0
    except Exception as e:
        print_error(f"Check failed: {e}")
        return 1


def run_fmt(input_path: str, write: bool = False) -> int:
    """Format the grammar."""
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        formatter = ConstrictorFormatter(content)
        formatted_code = formatter.format()

        if write:
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(formatted_code)
            print_success(f"Formatted {input_path}")
        else:
            print(formatted_code)
        return 0
    except Exception as e:
        print_error(f"Format failed: {e}")
        return 1


def run_test(input_path: str, verbose: bool = False) -> int:
    """Run tests defined in the grammar without generating files."""
    logger = Logger(use_color=True, verbose=verbose)

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return 1

    try:
        with open(input_path, "r", encoding="utf-8") as file:
            content = file.read()

        acantho_parser = Parser()
        grammars = acantho_parser.parse(content)

        if not grammars:
            logger.warn("No grammars found.")
            return 0

        all_passed = True
        for grammar in grammars:
            if not grammar.tests:
                print_warning(f"No tests found in grammar {grammar.name}")
                continue

            print_info(f"Testing grammar: {grammar.name}")
            generator = CodeGenerator(grammar, enable_recovery=True)
            code = generator.generate()

            success = run_tests_in_memory(grammar, code, logger)
            if not success:
                all_passed = False

        if all_passed:
            print_success("All tests passed!")
            return 0
        else:
            print_error("Some tests failed.")
            return 1

    except Exception as e:
        logger.error(f"Test run failed: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        return 1
