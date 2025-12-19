import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from cli.app import main
from cli.commands import run_init, run_build, run_check, run_fmt, run_test


class TestCLI(unittest.TestCase):
    @patch("cli.app.run_init")
    def test_init_command(self, mock_init):
        mock_init.return_value = 0
        test_args = ["acanthophis", "init", "MyGrammar"]
        with patch.object(sys, "argv", test_args):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)
        mock_init.assert_called_once_with("MyGrammar", ".")

    @patch("cli.app.run_build")
    def test_build_command(self, mock_build):
        mock_build.return_value = 0
        test_args = ["acanthophis", "build", "calc.apy"]
        with patch.object(sys, "argv", test_args):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)
        mock_build.assert_called_once()

    @patch("cli.app.run_check")
    def test_check_command(self, mock_check):
        mock_check.return_value = 0
        test_args = ["acanthophis", "check", "calc.apy"]
        with patch.object(sys, "argv", test_args):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)
        mock_check.assert_called_once()

    @patch("cli.app.run_fmt")
    def test_fmt_command(self, mock_fmt):
        mock_fmt.return_value = 0
        test_args = ["acanthophis", "fmt", "calc.apy"]
        with patch.object(sys, "argv", test_args):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)
        mock_fmt.assert_called_once()

    @patch("cli.app.run_test")
    def test_test_command(self, mock_test):
        mock_test.return_value = 0
        test_args = ["acanthophis", "test", "calc.apy"]
        with patch.object(sys, "argv", test_args):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)
        mock_test.assert_called_once()


if __name__ == "__main__":
    unittest.main()
