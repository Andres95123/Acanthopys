from __future__ import annotations
import sys
import os
from version import __version__


class Colors:
    """ANSI color codes for terminal output"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


def print_banner():
    """Print a beautiful banner for the CLI"""
    banner = f"""
{Colors.BOLD}{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║                      🐍 ACANTHOPYS 🐍                        ║
║                                                               ║
║              PEG Parser Generator & Toolchain                 ║
║                      Version {__version__:<27}  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)


def print_success(msg: str):
    print(f"{Colors.GREEN}✔ {msg}{Colors.RESET}")


def print_error(msg: str):
    print(f"{Colors.RED}✘ {msg}{Colors.RESET}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")
