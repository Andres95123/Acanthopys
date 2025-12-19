# Acanthophis 🐍

**Acanthophis** is a modern, robust, and feature-rich **PEG (Parsing Expression Grammar) Parser Generator** for Python. 

It is designed to solve the common pitfalls of traditional PEG parsers by implementing advanced features like **Left Recursion Support** and **Automatic Error Recovery**, while maintaining a simple and elegant syntax.

## ✨ Key Features

- **🔄 Left Recursion Support**: Implements Warth's algorithm to handle direct left recursion. You can write natural grammars like `Expr: Expr + Term` without infinite loops.
- **🛡️ Error Recovery**: Built-in "Panic Mode" recovery. The generated parsers don't just crash on the first error; they synchronize and report multiple issues.
- **⚡ Packrat Memoization**: Guarantees linear **O(n)** parse time by caching results.
- **🧪 Integrated TDD**: Define unit tests directly inside your grammar file. The generator verifies them before producing code.
- **🌳 Clean AST Generation**: Automatically generates Python dataclasses for your Abstract Syntax Tree.
- **🐍 Pure Python**: Generates standalone, dependency-free Python 3 code.

---

## 🚀 Getting Started

### Installation

Currently, Acanthophis is available via source. Clone the repository:

```bash
git clone https://github.com/Andres95123/Acanthopys.git
cd Acanthopys
```

### Your First Grammar

Create a file named `calc.apy`:

```acanthophis
grammar Calculator:
    tokens:
        NUMBER: \d+
        PLUS: \+
        WS: skip \s+
    end

    start rule Expr:
        | left:Expr PLUS right:Term -> Add(left, right)
        | val:Term -> pass
    end

    rule Term:
        | n:NUMBER -> Num(int(n))
    end

    test MyTests:
        "1 + 2" => Yields(Add(Num(1), Num(2)))
        "1 + 2 + 3" => Yields(Add(Add(Num(1), Num(2)), Num(3)))
    end
end
```

### Generate the Parser

Run the generator CLI:

```bash
# Initialize a new project
acanthophis init Calculator

# Build the parser
acanthophis build Calculator.apy

# Run tests
acanthophis test Calculator.apy

# Start REPL
acanthophis repl Calculator.apy
```

This will:
1. Parse your grammar.
2. **Run the integrated tests** (`MyTests`).
3. If tests pass, generate `Calculator_parser.py`.

### Use the Parser

The generated parser provides a clean, static API for easy integration.

```python
from Calculator_parser import Parser

# Parse text directly using the static method
result = Parser.parse("10 + 20")

# The result is a ParseResult dataclass
if result.is_valid:
    # Access the generated AST
    print(f"Success! AST: {result.ast}")
    # Output: Success! AST: Add(Num(10), Num(20))
else:
    # Handle errors gracefully
    print(f"Parsing failed with {len(result.errors)} errors:")
    for error in result.errors:
        print(f" - {error.message} at line {error.line}, col {error.column}")

# You can also access the raw tokens
print(f"Tokens: {result.tokens}")
```

### The `ParseResult` Object
The `Parser.parse()` method returns a `ParseResult` object with the following fields:
*   `ast`: The generated Abstract Syntax Tree (or `None` if parsing failed completely).
*   `errors`: A list of `ParseError` objects. If empty, parsing was successful.
*   `tokens`: A list of `Token` objects produced by the lexer.
*   `is_valid`: A boolean property (`True` if no errors occurred).

---

## 📖 Language Reference

Acanthophis uses a custom `.apy` file format that is intuitive and concise.

### 1. Tokens
Defined in the `tokens` block using Python Regex.
*   **Priority**: Top-to-bottom. Define specific keywords before general identifiers.
*   **Skip**: Use `skip` to ignore tokens (like whitespace) in the AST, though they are still consumed.

```acanthophis
tokens:
    IF: if              # Keyword
    ID: [a-z]+          # Identifier
    WS: skip \s+        # Ignored
end
```

### 2. Rules
Rules define the structure of your language.
*   **`start rule`**: Marks the entry point of the grammar.
*   **Operators**:
    *   `name:Rule` : Match `Rule` and bind result to `name`.
    *   `Rule?` : Optional (0 or 1).
    *   `Rule*` : Zero or more.
    *   `Rule+` : One or more.
    *   `|` : Ordered choice (Try first, if fails, try next).

### 3. AST Actions (`->`)
Define how to build the AST node for a rule.
*   `-> NodeName(arg1, arg2)`: Creates a class `NodeName` with the given arguments.
*   `-> pass`: Returns the value of the matched child directly (useful for wrapper rules).

```acanthophis
rule Atom:
    | n:NUMBER -> Num(n)
    | LPAREN e:Expr RPAREN -> pass  # Returns 'e' directly
end
```

### 4. Check Guards (`check ...`)
Add semantic validation or custom logic directly in your grammar.
*   Syntax: `check CONDITION then CODE [else then CODE]`
*   Executes Python code after a successful match.
*   Useful for semantic checks (e.g., "number must be positive") or side effects.

```acanthophis
rule PositiveNumber:
    | n:NUMBER -> int(n) check int(n) > 0 then print("Valid") else then print("Invalid")
end
```

### 5. Integrated Tests
Write tests to ensure your grammar works as expected.
*   `Yields(...)`: Asserts the parse result matches the structure.
*   `Fail`: Asserts the input fails to parse.

```acanthophis
test MathTests Expr:
    "1+1" => Yields(Add(Num(1), Num(1)))
    "1+"  => Fail
end
```

---

## 🛠️ Advanced Features

### Left Recursion
Traditional PEG parsers cannot handle left recursion (e.g., `A <- A 'b' / 'a'`). Acanthophis **can**.
This allows you to write left-associative operators naturally:

```acanthophis
# This works perfectly!
rule Expr:
    | left:Expr MINUS right:Term -> Sub(left, right)
    | t:Term -> pass
end
```
Input `1 - 2 - 3` parses as `((1 - 2) - 3)`.

### Error Recovery
By default, generated parsers include error recovery. If a syntax error occurs, the parser attempts to synchronize and continue parsing to report multiple errors.

*   **Disable**: Use `--no-recovery` flag in CLI.
*   **Runtime**: Pass `enable_recovery=True` to the `Parser` constructor.

---

## 🧰 CLI Reference

Acanthophis provides a modern CLI with subcommands for every stage of development.

### Usage
```bash
python -m acanthophis [command] [options]
```

| Command | Description                                      | Example                         |
| :------ | :----------------------------------------------- | :------------------------------ |
| `init`  | Initialize a new project structure.              | `acanthophis init MyProject`    |
| `build` | Compile grammar files into Python parsers.       | `acanthophis build grammar.apy` |
| `check` | Validate grammar syntax without generating code. | `acanthophis check grammar.apy` |
| `test`  | Run integrated tests defined in the grammar.     | `acanthophis test grammar.apy`  |
| `repl`  | Start an interactive shell for your grammar.     | `acanthophis repl grammar.apy`  |
| `fmt`   | Format grammar files (standardizes indentation). | `acanthophis fmt grammar.apy`   |

### Common Options
*   `-v, --verbose`: Enable detailed logging.
*   `--no-color`: Disable colored output.
*   `--version`: Show version information.

### Build Options
*   `-o, --output`: Specify output directory (default: current dir).
*   `--no-recovery`: Disable error recovery generation.

### Interactive REPL
A powerful REPL is included to test your grammars interactively with AST visualization and error reporting.

```bash
python demo/repl.py
```
*   Edit `demo/repl.py` to point to your generated parser module if needed.

---

## 📂 Project Structure

```
Acanthophis/
├── acanthophis/          # Core Source Code
│   ├── main.py           # Entry point
│   ├── parser/           # The Grammar Parser (bootstrapping)
│   └── utils/
│       └── generators/   # Code Generators (Python)
├── demo/                 # Examples & Tools
│   ├── calculator.apy    # Advanced Demo Grammar
│   └── repl.py           # Interactive REPL
└── tests/                # Unit Tests
```

---

## 📄 License

BSD Licence
