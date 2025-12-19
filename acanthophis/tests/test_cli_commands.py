import os
import pytest
import textwrap
from cli.commands import run_init, run_build, run_check, run_fmt, run_test
from cli.repl import run_repl
from cli.app import main
from unittest.mock import patch, MagicMock


def test_run_test(tmp_path):
    grammar_file = tmp_path / "TestTest.apy"
    grammar_file.write_text(
        textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end
        rule Test:
            | x:ID -> x
        end
        test Test:
            "abc" => Success
        end
    end
    """),
        encoding="utf-8",
    )

    ret = run_test(str(grammar_file))
    assert ret == 0

    # Test fail
    grammar_file.write_text(
        textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end
        rule Test:
            | x:ID -> x
        end
        test Test:
            "123" => Success
        end
    end
    """),
        encoding="utf-8",
    )

    ret = run_test(str(grammar_file))
    assert ret == 1


def test_run_test_verbose(tmp_path):
    grammar_file = tmp_path / "TestVerbose.apy"
    grammar_file.write_text(
        textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end
        rule Test:
            | x:ID -> x
        end
        test Test:
            "abc" => Success
        end
    end
    """),
        encoding="utf-8",
    )

    ret = run_test(str(grammar_file), verbose=True)
    assert ret == 0


def test_run_repl(tmp_path):
    grammar_file = tmp_path / "TestRepl.apy"
    grammar_file.write_text(
        textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end
        rule Test:
            | x:ID -> x
        end
    end
    """),
        encoding="utf-8",
    )

    # Mock input to exit immediately
    with patch("builtins.input", side_effect=["exit"]):
        ret = run_repl(str(grammar_file), watch=False)
        assert ret == 0

    # Test invalid file
    ret = run_repl(str(tmp_path / "NonExistent.apy"))
    assert ret == 1


@patch("time.sleep")  # Not used in repl watch but good to mock if it was
@patch("os.path.getmtime")
def test_run_repl_watch(mock_mtime, mock_sleep, tmp_path):
    grammar_file = tmp_path / "TestReplWatch.apy"
    grammar_file.write_text(
        textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end
        rule Test:
            | x:ID -> x
        end
    end
    """),
        encoding="utf-8",
    )

    # Mock mtime to change
    # Initial load (getmtime called once)
    # Loop 1: check mtime (same)
    # Loop 2: check mtime (changed) -> reload -> getmtime called again? No, load_parser reads file.
    # Wait, run_repl calls load_parser which reads file.
    # It calls getmtime inside the loop.

    mock_mtime.side_effect = [100, 100, 200, 200, 200]

    # Mock input to exit after reload
    # Input called in loop.
    # Loop 1: mtime same. input called.
    # Loop 2: mtime changed. reload. input called.
    with patch("builtins.input", side_effect=["", "exit"]):
        ret = run_repl(str(grammar_file), watch=True)
        assert ret == 0


def test_run_repl_error(tmp_path):
    grammar_file = tmp_path / "TestReplError.apy"
    grammar_file.write_text(
        textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end
        rule Test:
            | x:ID -> x
        end
    end
    """),
        encoding="utf-8",
    )

    # Mock input to cause parse error then exit
    with patch("builtins.input", side_effect=["123", "exit"]):
        ret = run_repl(str(grammar_file), watch=False)
        assert ret == 0


def test_run_init(tmp_path):
    os.chdir(tmp_path)
    ret = run_init("TestGrammar", str(tmp_path))
    assert ret == 0
    assert (tmp_path / "TestGrammar.apy").exists()

    # Test existing file
    ret = run_init("TestGrammar", str(tmp_path))
    assert ret == 1


def test_run_build(tmp_path):
    grammar_file = tmp_path / "Test.apy"
    grammar_file.write_text(
        textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end
        rule Test:
            | x:ID -> x
        end
    end
    """),
        encoding="utf-8",
    )

    ret = run_build(str(grammar_file), str(tmp_path), no_tests=True)
    assert ret == 0
    assert (tmp_path / "Test_parser.py").exists()

    # Test dry run
    ret = run_build(str(grammar_file), str(tmp_path), no_tests=True, dry_run=True)
    assert ret == 0

    # Test invalid file
    ret = run_build(str(tmp_path / "NonExistent.apy"), str(tmp_path))
    assert ret == 1


def test_run_check(tmp_path):
    grammar_file = tmp_path / "Test.apy"
    grammar_file.write_text(
        textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end
        rule Test:
            | x:ID -> x
        end
    end
    """),
        encoding="utf-8",
    )

    ret = run_check(str(grammar_file))
    assert ret == 0

    # Test invalid grammar
    grammar_file.write_text("invalid", encoding="utf-8")
    # run_check might raise exception or return 1 depending on implementation
    # It catches exceptions and prints error, returns 1
    ret = run_check(str(grammar_file))
    assert ret == 1


def test_run_fmt(tmp_path):
    grammar_file = tmp_path / "Test.apy"
    original_content = """grammar Test:
tokens:
ID: [a-z]+
end
rule Test:
| x:ID -> x
end
end
"""
    grammar_file.write_text(original_content, encoding="utf-8")

    # Test stdout (no write)
    ret = run_fmt(str(grammar_file), write=False)
    assert ret == 0
    assert grammar_file.read_text(encoding="utf-8") == original_content

    # Test write
    ret = run_fmt(str(grammar_file), write=True)
    assert ret == 0
    # Formatter should have formatted it
    formatted = grammar_file.read_text(encoding="utf-8")
    assert "grammar Test:" in formatted
    assert "    tokens:" in formatted  # Indentation


def test_run_build_with_tests(tmp_path):
    grammar_file = tmp_path / "TestWithTests.apy"
    grammar_file.write_text(
        textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end
        rule Test:
            | x:ID -> x
        end
        test Test:
            "abc" => Success
        end
    end
    """),
        encoding="utf-8",
    )

    ret = run_build(str(grammar_file), str(tmp_path), no_tests=False)
    assert ret == 0


def test_run_build_fail_tests(tmp_path):
    grammar_file = tmp_path / "TestFail.apy"
    grammar_file.write_text(
        textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end
        rule Test:
            | x:ID -> x
        end
        test Test:
            "123" => Success # Should fail lexing
        end
    end
    """),
        encoding="utf-8",
    )

    ret = run_build(str(grammar_file), str(tmp_path), no_tests=False)
    assert ret == 1


@patch("time.sleep")
@patch("os.path.getmtime")
def test_run_build_watch(mock_mtime, mock_sleep, tmp_path):
    grammar_file = tmp_path / "TestWatch.apy"
    grammar_file.write_text(
        textwrap.dedent("""
    grammar Test:
        tokens:
            ID: [a-z]+
        end
        rule Test:
            | x:ID -> x
        end
    end
    """),
        encoding="utf-8",
    )

    # Mock mtime to change
    mock_mtime.side_effect = [
        100,
        100,
        200,
        200,
    ]  # Initial, loop 1 check, loop 2 check (change), loop 3 check

    # Mock sleep to raise KeyboardInterrupt after a few calls
    mock_sleep.side_effect = [None, KeyboardInterrupt]

    ret = run_build(str(grammar_file), str(tmp_path), watch=True)
    assert ret == 0
