import os
import sys
import time
from contextlib import contextmanager
from typing import Generator


class Ansi:
    CYAN = "\033[96m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    PURPLE = "\033[95m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def _supports_color() -> bool:
    if os.environ.get("ACANTHOPHIS_NO_COLOR"):
        return False
    if sys.platform == "win32":
        # Modern Windows terminals generally support ANSI; allow override
        return True
    return sys.stdout.isatty()


class Logger:
    def __init__(self, use_color: bool | None = None, verbose: bool = False) -> None:
        self.use_color = _supports_color() if use_color is None else use_color
        self.verbose_mode = verbose

    def _fmt(self, level: str, color: str, msg: str) -> str:
        if self.use_color:
            return f"{color}{Ansi.BOLD}[{level}]{Ansi.RESET} {msg}"
        return f"[{level}] {msg}"

    def info(self, msg: str) -> None:
        print(self._fmt("INFO", Ansi.CYAN, msg))

    def success(self, msg: str) -> None:
        print(self._fmt("SUCCESS", Ansi.GREEN, msg))

    def error(self, msg: str) -> None:
        print(self._fmt("ERROR", Ansi.RED, msg))

    def warn(self, msg: str) -> None:
        print(self._fmt("WARN", Ansi.PURPLE, msg))

    def debug(self, msg: str) -> None:
        if self.verbose_mode:
            prefix = f"{Ansi.BLUE}[DEBUG]{Ansi.RESET}" if self.use_color else "[DEBUG]"
            content = f"{Ansi.DIM}{msg}{Ansi.RESET}" if self.use_color else msg
            print(f"{prefix} {content}")

    def hint(self, msg: str) -> None:
        # softer level used within details
        if self.use_color:
            print(f"  {Ansi.YELLOW}{msg}{Ansi.RESET}")
        else:
            print(f"  {msg}")

    @contextmanager
    def timer(self, description: str) -> Generator[None, None, None]:
        start = time.perf_counter()
        yield
        end = time.perf_counter()
        duration = end - start
        if self.verbose_mode:
            self.debug(f"{description} took {duration:.4f}s")
        else:
            # Optional: print timing info even in non-verbose if it's significant?
            # For now, let's keep it simple or maybe print it as info if it's a major step.
            pass
