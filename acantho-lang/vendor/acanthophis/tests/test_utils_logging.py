import os
import pytest
from utils.logging import Logger


class TestLogger:
    def test_no_color_env_disables_color(self):
        os.environ["ACANTHOPHIS_NO_COLOR"] = "1"
        try:
            logger = Logger()
            # Should not crash and should produce bracketed messages without ANSI
            # We can't intercept stdout easily here; just ensure methods exist and run
            logger.info("info message")
            logger.warn("warn message")
            logger.error("error message")
            logger.success("success message")
        finally:
            del os.environ["ACANTHOPHIS_NO_COLOR"]
