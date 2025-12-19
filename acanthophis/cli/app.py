from __future__ import annotations

import argparse
import os
import sys
import time
import json

from parser import Parser
from utils.logging import Logger
from testing.runner import run_tests_in_memory
from lang.file_texts import AUTOMATIC_GENERATED_TEXT
from utils.generators import CodeGenerator
from version import __version__
from linter.venom_linter import VenomLinter
from formatter.constrictor_formatter import ConstrictorFormatter


def serialize(obj):
    if isinstance(obj, list):
        return [serialize(i) for i in obj]
    if hasattr(obj, "__dict__"):
        return {k: serialize(v) for k, v in obj.__dict__.items()}
    return obj


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Acanthopys: PEG Parser Generator & Toolchain"
    )
    parser.add_argument(
        "--version", action="version", version=f"Acanthopys v{__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate parser from grammar")
    gen_parser.add_argument("input", help="Input .acantho grammar file")
    gen_parser.add_argument("-o", "--output", help="Output directory", default=".")
    gen_parser.add_argument(
        "--no-tests", action="store_true", help="Disable integrated tests execution"
    )
    gen_parser.add_argument(
        "--tests",
        action="store_true",
        help="Run ONLY the integrated tests and exit. Does not generate output files.",
    )
    gen_parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI colors in logs"
    )
    gen_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging"
    )
    gen_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the full generation process (including tests) but do NOT write output files.",
    )
    gen_parser.add_argument(
        "--no-recovery",
        action="store_true",
        help="Disable error recovery mode (Panic Mode). By default, parsers are generated with recovery enabled.",
    )

    # Lint command
    lint_parser = subparsers.add_parser("lint", help="Lint a grammar file")
    lint_parser.add_argument("input", help="Input .acantho grammar file")
    lint_parser.add_argument(
        "--json", action="store_true", help="Output as JSON", default=True
    )

    # Format command
    fmt_parser = subparsers.add_parser("format", help="Format a grammar file")
    fmt_parser.add_argument("input", help="Input .acantho grammar file")
    fmt_parser.add_argument(
        "--write", action="store_true", help="Write changes to file"
    )

    # AST command
    ast_parser = subparsers.add_parser("ast", help="Show AST")
    ast_parser.add_argument("input", help="Input .acantho grammar file")

    return parser


def run_generate(args: argparse.Namespace) -> int:
    logger = Logger(use_color=not args.no_color, verbose=args.verbose)
    start_time = time.perf_counter()

    input_path = args.input
    output_dir = args.output
    no_tests = args.no_tests
    only_tests = args.tests
    dry_run = args.dry_run
    enable_recovery = not args.no_recovery

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return 1

    logger.info(f"Reading grammar from {input_path}...")

    try:
        with logger.timer("Reading file"):
            with open(input_path, "r", encoding="utf-8") as file:
                content = file.read()

        acantho_parser = Parser()
        try:
            with logger.timer("Parsing grammar"):
                grammars = acantho_parser.parse(content)
        except Exception as e:  # noqa: BLE001 - DX
            logger.error(f"Failed to parse grammar file '{input_path}':")
            logger.error(f"  {e}")
            return 1

        if not grammars:
            logger.warn("No grammars found in file.")
            return 0

        for grammar in grammars:
            logger.info(f"Generating parser for grammar: {grammar.name}")
            if enable_recovery:
                logger.info("  - Recovery Mode: ENABLED")

            with logger.timer(f"Code generation for {grammar.name}"):
                generator = CodeGenerator(grammar, enable_recovery=enable_recovery)
                code = generator.generate()

            if grammar.tests:
                if no_tests:
                    logger.warn(
                        f"Skipping tests for {grammar.name}. It is highly recommended to run tests to ensure parser correctness."
                    )
                else:
                    logger.info(f"Running integrated tests for grammar: {grammar.name}")

                    # Run tests in memory
                    success = run_tests_in_memory(grammar, code, logger)
                    if not success:
                        logger.error(f"Tests failed for grammar: {grammar.name}")
                        return 1

            if only_tests:
                continue

            if not dry_run:
                output_filename = f"{grammar.name}_parser.py"
                output_path = os.path.join(output_dir, output_filename)

                # Ensure output directory exists
                os.makedirs(output_dir, exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(code)
                logger.info(f"Parser written to {output_path}")
            else:
                logger.info("Dry run: No files written.")

        duration = time.perf_counter() - start_time
        logger.info(f"Done in {duration:.4f}s.")
        return 0

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def run_lint(args: argparse.Namespace) -> int:
    try:
        linter = VenomLinter(args.input)
        results = linter.lint()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for diag in results:
                print(f"{diag['file']}:{diag['line']} - {diag['message']}")
        return 0 if not any(d["severity"] == "Error" for d in results) else 1
    except Exception as e:
        print(
            json.dumps(
                [
                    {
                        "line": 1,
                        "message": str(e),
                        "severity": "Error",
                        "file": args.input,
                    }
                ]
            )
        )
        return 1


def run_format(args: argparse.Namespace) -> int:
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()

        formatter = ConstrictorFormatter(content)
        formatted_code = formatter.format()

        if args.write:
            with open(args.input, "w", encoding="utf-8") as f:
                f.write(formatted_code)
        else:
            print(formatted_code)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def run_ast(args: argparse.Namespace) -> int:
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()

        parser = Parser()
        grammars = parser.parse(content)
        print(json.dumps(serialize(grammars), indent=2))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def run_cli(args: argparse.Namespace) -> int:
    if args.command == "generate":
        return run_generate(args)
    elif args.command == "lint":
        return run_lint(args)
    elif args.command == "format":
        return run_format(args)
    elif args.command == "ast":
        return run_ast(args)
    elif args.command is None:
        print("Please specify a command: generate, lint, format, ast")
        return 1
    return 0


def main() -> None:
    # Force UTF-8 for stdout/stderr to avoid encoding issues with special characters
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            # Python < 3.7 or some environments
            pass

    parser = build_arg_parser()
    args = parser.parse_args()
    code = run_cli(args)
    if code:
        sys.exit(code)
