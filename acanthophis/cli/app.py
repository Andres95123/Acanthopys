from __future__ import annotations

import argparse
import sys
import os

from version import __version__
from cli.console import Colors, print_banner, print_error
from cli.commands import run_init, run_build, run_check, run_fmt, run_test
from cli.repl import run_repl


class ColorfulHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom help formatter with colors and better structure"""

    def __init__(self, prog, **kwargs):
        self.use_colors = sys.stdout.isatty() and os.name != "nt" or os.getenv("TERM")
        super().__init__(prog, **kwargs)

    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = f"{Colors.BOLD}{Colors.CYAN}Usage:{Colors.RESET} "
        return super()._format_usage(usage, actions, groups, prefix)

    def _format_action(self, action):
        result = super()._format_action(action)
        if self.use_colors:
            if action.option_strings:
                for opt in action.option_strings:
                    result = result.replace(opt, f"{Colors.CYAN}{opt}{Colors.RESET}")
            if action.metavar:
                result = result.replace(
                    str(action.metavar),
                    f"{Colors.GREEN}{action.metavar}{Colors.RESET}",
                )
        return result

    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = f"{Colors.BOLD}{Colors.CYAN}Usage:{Colors.RESET} "
        return super().add_usage(usage, actions, groups, prefix)

    def start_section(self, heading):
        if self.use_colors and heading:
            heading = f"{Colors.BOLD}{Colors.CYAN}{heading}:{Colors.RESET}"
        return super().start_section(heading)


def build_arg_parser() -> argparse.ArgumentParser:
    description = f"""{Colors.BOLD}Acanthopys{Colors.RESET} - The Modern PEG Compiler-Compiler

{Colors.BOLD}Description:{Colors.RESET}
  Acanthopys is a next-generation parser generator designed to replace Bison, Yacc, and Flex.
  It offers a unified toolchain for building, testing, and debugging grammars with ease.

{Colors.BOLD}Commands:{Colors.RESET}
  {Colors.CYAN}init{Colors.RESET}      Initialize a new grammar project
  {Colors.CYAN}build{Colors.RESET}     Compile grammar to Python code
  {Colors.CYAN}check{Colors.RESET}     Lint and validate grammar file
  {Colors.CYAN}fmt{Colors.RESET}       Format grammar file
  {Colors.CYAN}test{Colors.RESET}      Run embedded tests
  {Colors.CYAN}repl{Colors.RESET}      Start interactive REPL
"""

    parser = argparse.ArgumentParser(
        prog="acanthophis",
        description=description,
        formatter_class=ColorfulHelpFormatter,
        add_help=False,
    )

    parser.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit"
    )
    parser.add_argument(
        "--version", action="version", version=f"Acanthopys v{__version__}"
    )

    subparsers = parser.add_subparsers(
        dest="command", title="Commands", metavar="<command>"
    )

    # INIT
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new grammar project",
        formatter_class=ColorfulHelpFormatter,
    )
    init_parser.add_argument("name", help="Name of the grammar/project")
    init_parser.add_argument("-o", "--output", default=".", help="Output directory")

    # BUILD (Generate)
    build_parser = subparsers.add_parser(
        "build",
        aliases=["generate"],
        help="Compile grammar to Python code",
        formatter_class=ColorfulHelpFormatter,
    )
    build_parser.add_argument("input", metavar="FILE", help="Path to .apy file")
    build_parser.add_argument("-o", "--output", default=".", help="Output directory")
    build_parser.add_argument(
        "--no-tests", action="store_true", help="Skip running tests"
    )
    build_parser.add_argument(
        "--dry-run", action="store_true", help="Don't write files"
    )
    build_parser.add_argument(
        "--no-recovery", action="store_true", help="Disable error recovery"
    )
    build_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    build_parser.add_argument(
        "--watch", action="store_true", help="Watch for changes and rebuild"
    )

    # CHECK (Lint)
    check_parser = subparsers.add_parser(
        "check",
        aliases=["lint"],
        help="Lint and validate grammar file",
        formatter_class=ColorfulHelpFormatter,
    )
    check_parser.add_argument("input", metavar="FILE", help="Path to .apy file")
    check_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # FMT (Format)
    fmt_parser = subparsers.add_parser(
        "fmt",
        aliases=["format"],
        help="Format grammar file",
        formatter_class=ColorfulHelpFormatter,
    )
    fmt_parser.add_argument("input", metavar="FILE", help="Path to .apy file")
    fmt_parser.add_argument(
        "--write", action="store_true", help="Write changes to file"
    )

    # TEST
    test_parser = subparsers.add_parser(
        "test", help="Run embedded tests", formatter_class=ColorfulHelpFormatter
    )
    test_parser.add_argument("input", metavar="FILE", help="Path to .apy file")
    test_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )

    # REPL
    repl_parser = subparsers.add_parser(
        "repl", help="Start interactive REPL", formatter_class=ColorfulHelpFormatter
    )
    repl_parser.add_argument("input", metavar="FILE", help="Path to .apy file")
    repl_parser.add_argument("--rule", help="Start rule to use")
    repl_parser.add_argument(
        "--no-watch", action="store_true", help="Disable auto-reload on file change"
    )

    return parser


def main() -> None:
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    parser = build_arg_parser()

    if len(sys.argv) == 1:
        print_banner()
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    cmd = args.command

    ret = 0
    if cmd in ["init"]:
        ret = run_init(args.name, args.output)
    elif cmd in ["build", "generate"]:
        ret = run_build(
            args.input,
            args.output,
            args.no_tests,
            args.dry_run,
            not args.no_recovery,
            args.verbose,
            args.watch,
        )
    elif cmd in ["check", "lint"]:
        ret = run_check(args.input, args.json)
    elif cmd in ["fmt", "format"]:
        ret = run_fmt(args.input, args.write)
    elif cmd in ["test"]:
        ret = run_test(args.input, args.verbose)
    elif cmd in ["repl"]:
        ret = run_repl(args.input, args.rule, not args.no_watch)
    else:
        parser.print_help()
        ret = 1

    sys.exit(ret)


if __name__ == "__main__":
    main()
