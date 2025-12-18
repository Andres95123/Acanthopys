*# Acanthopys: PEG Parser Generator

Acanthopys is a professional tool for generating Packrat (PEG) parsers in Python. Designed to be simple, elegant, and powerful, it allows defining complex grammars, testing them integrally, and generating optimized Python code ready to use.

## Main Features

- **PEG Grammars**: Full support for Parsing Expression Grammars, eliminating ambiguity.
- **Memoization (Packrat)**: Guarantees linear O(n) runtime through result caching.
- **Integrated Tests**: Define test cases directly in the grammar file for smooth TDD (Test Driven Development).
- **AST Generation**: Automatic creation of Abstract Syntax Tree (AST) nodes with a clean and readable representation.
- **Multiple Grammars**: Support for defining multiple grammars in a single .apy file.
- **Robust CLI**: Command-line interface with colors, flags, and detailed error reports.

## Installation

No complex installation required. Make sure you have Python 3.8+ installed.

```bash
git clone https://github.com/Andres95123/Acanthopys.git
cd acanthopys
```

## Basic Usage

### 1. Define the Grammar (.apy)

Create a file with .apy extension. The basic structure is:

```acantho
grammar GrammarName:
    tokens:
        # Token definitions (Name: Regex)
        # Important: Order matters (priority from top to bottom)
        NUMBER: \d+
        PLUS: \+
        WS: skip \s+  # 'skip' ignores the token (useful for spaces)
    end

    # 'start rule' defines the parser's entry point
    start rule StartRule:
        # Production rules
        | left:Term PLUS right:StartRule -> AddNode(left, right)
        | child:Term -> pass  # 'pass' promotes the result without creating a node
    end

    rule Term:
        | value:NUMBER -> NumberNode(float(value))
    end

    # Test suite for the default rule (StartRule)
    test MyTests:
        "1 + 2" => Yields(AddNode(NumberNode(1.0), NumberNode(2.0)))
        "1 + a" => Fail
    end

    # Specific test suite for a rule (Term)
    test TermTests Term:
        "42" => Yields(NumberNode(42.0))
    end
end
```

### 2. Generate the Parser

Run the main script passing your grammar file:

```bash
python acanthopys/main.py my_grammar.apy
```

This will generate a file `GrammarName_parser.py` in the current directory (or specified with -o).

### 3. CLI Options

- `input`: Input .apy file.
- `-o`, `--output`: Output directory for generated files (default: `.`).
- `--no-tests`: Disables running integrated tests (not recommended).
- `--tests`: Runs only tests without generating the parser file. Ideal for iterative development and CI/CD.

## Detailed Syntax

### Tokens
Tokens are defined with Python regex expressions.
- `NAME: PATTERN`
- `NAME: skip PATTERN` (The token is consumed but not emitted to the parser).

**Important:**
1. **Order:** Definition order matters. Tokens are evaluated from top to bottom. Define more specific tokens before general ones.
   - Example: `int` (keyword) must go before `[a-zA-Z_]\w*` (general identifier)
   - Example: `==` must go before `=`
   - Example: Comments should go at the beginning so `/` is not taken as division
2. **Spaces:** The generator takes the pattern as is (including spaces). If you use the `|` (OR) operator, make sure not to leave spaces around unless you want the space to be part of the pattern.
   - Correct: `COMMENT: //.*|/\*.*\*/`
   - Incorrect (if you don't want spaces): `COMMENT: //.* | /\*.*\*/`

### Rules
Rules define the syntactic structure.

- **Start Rule**: You can mark a rule as `start rule Name:` to indicate it is the main entry point of the parser.
  - If **not specified**, the first defined rule will be used (with a warning recommending to add `start`).
  - If there are **multiple** rules marked with `start`, an error is generated.
  - Example: `start rule Expression:` marks `Expression` as the entry point.
- `|` starts an alternative.
- `name:Type` captures a token or the result of another rule in a variable.
- `-> Node` defines which AST node to create.
  - `-> ClassName(arg1, arg2)`: Creates an instance of `ClassName`.
  - `-> pass`: Returns the value of the captured variable.
    - If there is a single captured variable, returns its value.
    - If there are no variables but a single non-literal term (e.g., `| NUMBER -> pass` or `| '(' Expr ')' -> pass`), returns the token/value of that term automatically.
    - If there are no variables or capturable terms, returns `None`.

### Tests
The `test` blocks allow verifying the grammar at compile time.

Syntax: `test SuiteName [TargetRule]:`

- **TargetRule (Optional)**: If specified, tests will run against that specific rule instead of the start rule. Ideal for testing isolated components.
  - Example: `test operandTests Operand:` → tests only the `Operand` rule.
  - If not specified, the start rule is used (marked with `start` or the first one).

Assertion types:
- `"input" => Success`: Expects parsing to be successful.
- `"input" => Fail`: Expects parsing to fail (useful for testing syntax errors).
- `"input" => Yields(Structure)`: Expects the resulting AST to exactly match the given structure.
  - Example: `'x : int' => Yields(DeclarationNode('x', 'int'))`
  - **Wildcard `...`**: You can use `...` inside a constructor to ignore internal arguments:
    - `'2 + 8' => Yields(AdditionNode(...))` → Verifies that the result is an `AdditionNode` regardless of its arguments.
    - `'(1 + 2) * 3' => Yields(MultiplicationNode(AdditionNode(...), ...))` → Verifies the structure but ignores internal details.
    - Useful for integration tests where only the node type matters, not exact values.

**Important about Yields:**
1. **Mandatory Syntax:** You must write `Yields(...)` - you cannot put the node directly.
   - ✅ Correct: `"1 + 2" => Yields(AddNode(1, 2))`
   - ❌ Incorrect: `"1 + 2" => AddNode(1, 2)`
2. **Token Representation:** Tokens are represented as strings with single quotes.
   - Example: If your rule captures an `identifier`, the test must use `'name'` not `"name"`
   - Example: `Variable('int', 'x')` for an `int` token and an `x` identifier
3. **Strict Comparison:** The comparison is exact, character by character (unless using `...`).

**Common Errors:**
- Forgetting `Yields(...)` → The system will detect and report a syntax error
- Using double quotes instead of single for tokens → The test will fail showing the difference
- Parenthesis errors → The system will detect unbalanced parentheses

## Examples

### Simple Calculator

```acantho
grammar Calc:
    tokens:
        NUM: \d+
        PLUS: \+
        WS: skip \s+
    end

    start rule Expr:
        | l:NUM PLUS r:Expr -> Add(l, r)
        | n:NUM -> Num(int(n))
    end
    
    test CalcTests:
        "1 + 2" => Yields(Add(Num(1), Num(2)))
        "5 + 3 + 2" => Yields(Add(...))  # Only verifies it's an Add
    end
    
    test NumTests Expr:
        "42" => Yields(Num(42))
    end
end
```

### Using the --tests Flag

For rapid development, you can run only the tests without generating the parser:

```bash
# Run only tests
python acanthopys/main.py my_grammar.apy --tests

# Generate the parser (with automatic tests)
python acanthopys/main.py my_grammar.apy

# Generate without running tests (not recommended)
python acanthopys/main.py my_grammar.apy --no-tests
```

### JSON Parser (Snippet)

```acantho
grammar JSON:
    tokens:
        STR: "[^"]*"
        ...
    end

    rule Value:
        | s:STR -> StringNode(s)
        | n:NUMBER -> NumberNode(float(n))
        ...
    end
end
```

## Known Limitations

- Does not support direct left recursion (due to PEG/Packrat nature).
- Token regex must be compatible with Python's `re` module.

## VS Code Support

To get syntax highlighting for .apy files, copy the `acantho-lang` folder to your VS Code extensions directory (`~/.vscode/extensions/`).
*