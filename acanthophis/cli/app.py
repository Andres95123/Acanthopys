from __future__ import annotations

import argparse
import os
import sys
import time

from parser import Parser
from utils.logging import Logger
from testing.runner import run_tests_in_memory
from lang.file_texts import AUTOMATIC_GENERATED_TEXT
from utils.generators import CodeGenerator
from version import __version__


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Acanthopys: PEG Parser Generator")
    parser.add_argument("input", help="Input .acantho grammar file")
    parser.add_argument("-o", "--output", help="Output directory", default=".")
    parser.add_argument(
        "--no-tests", action="store_true", help="Disable integrated tests execution"
    )
    parser.add_argument(
        "--tests",
        action="store_true",
        help="Run ONLY the integrated tests and exit. Does not generate output files.",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI colors in logs"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the full generation process (including tests) but do NOT write output files.",
    )
    parser.add_argument(
        "--no-recovery",
        action="store_true",
        help="Disable error recovery mode (Panic Mode). By default, parsers are generated with recovery enabled.",
    )
    parser.add_argument(
        "--version", action="version", version=f"Acanthopys v{__version__}"
    )
    return parser


def run_cli(args: argparse.Namespace) -> int:
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
                    with logger.timer(f"Tests for {grammar.name}"):
                        if not run_tests_in_memory(grammar, code, logger=logger):
                            logger.error(
                                f"Aborting generation for {grammar.name} due to test failures."
                            )
                            return 1
            else:
                logger.warn(
                    f"No tests defined for {grammar.name}. Skipping verification."
                )

            if only_tests:
                logger.info(
                    f"Tests passed for {grammar.name}. Skipping file generation (--tests flag active)."
                )
                continue

            if dry_run:
                logger.info(
                    f"Dry run: would write parser to {os.path.join(output_dir, f'{grammar.name}_parser.py')}"
                )
                continue

            output_file = os.path.join(output_dir, f"{grammar.name}_parser.py")
            with logger.timer(f"Writing output to {output_file}"):
                with open(output_file, "w", encoding="utf-8") as file:
                    file.write(f"{AUTOMATIC_GENERATED_TEXT}\n{code}")

            logger.success(f"Parser written to {output_file}")

        total_time = time.perf_counter() - start_time
        if args.verbose:
            logger.debug(f"Total execution time: {total_time:.4f}s")

        return 0

    except Exception as e:  # noqa: BLE001
        logger.error(f"An unexpected error occurred: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    code = run_cli(args)
    if code:
        sys.exit(code)
