# Acanthophis 🐍

> **The Python Parser Generator that feels like 2025.**

Acanthophis is a modern, developer-first **PEG Parser Generator** for Python. It turns your grammar files into robust, standalone Python parsers with zero dependencies.

Unlike traditional tools, Acanthophis is built for **Developer Experience (DX)**. It supports **Left Recursion** (so you can write natural math expressions), includes **Automatic Error Recovery** (Panic Mode), and has **Integrated Unit Testing** right in the grammar file.

---

## ⚡ Why Acanthophis?

*   **🧠 Intuitive**: Write grammars that look like your mental model. No more fighting with "left recursion" errors.
*   **🛡️ Robust**: Generated parsers don't crash on the first syntax error. They recover and report *all* errors.
*   **🧪 TDD-First**: Define tests alongside your rules. If the tests fail, the parser isn't generated.
*   **📦 Zero Dependencies**: The output is a single, pure Python file you can drop anywhere.
*   **🚀 Fast**: Uses Packrat Memoization for linear O(n) parsing performance.

---

## 🚀 Getting Started

### 1. Installation

Currently, Acanthophis is available via source.

```bash
# Clone the repository
git clone https://github.com/Andres95123/Acanthopys.git
cd Acanthopys

# (Optional) Add to your path or use via python -m
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### 2. Create a Project

Use the CLI to scaffold a new grammar file instantly.

```bash
python -m acanthophis init Calculator
```

This creates `Calculator.apy` with a starter grammar.

### 3. Define Your Grammar

Open `Calculator.apy`. The syntax is clean and Python-like.

```acanthophis
grammar Calculator:
    tokens:
        NUMBER: \d+
        PLUS: \+
        WS: skip \s+
    end

    start rule Expr:
        # Left recursion is fully supported!
        | left:Expr PLUS right:Term -> Add(left, right)
        | val:Term -> pass
    end

    rule Term:
        | n:NUMBER -> Num(int(n))
    end

    # Integrated Tests ensure your grammar works before you build
    test MyTests:
        "1 + 2" => Yields(Add(Num(1), Num(2)))
        "1 + 2 + 3" => Yields(Add(Add(Num(1), Num(2)), Num(3)))
    end
end
```

### 4. Test & Build

Run the tests defined in your grammar file:

```bash
python -m acanthophis test Calculator.apy
```

If everything looks green, generate the Python parser:

```bash
python -m acanthophis build Calculator.apy
```

This generates `Calculator_parser.py`.

### 5. Interactive REPL

Want to play with your language? Launch the REPL:

```bash
python -m acanthophis repl Calculator.apy
```

### 6. Watch Mode (New!)

Iterate faster by watching your grammar file for changes.

**REPL:**
The REPL automatically reloads when you save your grammar file (enabled by default).
```bash
python -m acanthophis repl Calculator.apy
# To disable:
python -m acanthophis repl Calculator.apy --no-watch
```

**Build:**
You can also watch for changes during build:
```bash
python -m acanthophis build Calculator.apy --watch
```

---

## ✨ New Features (v0.2)

### 1. Inline Literals
You no longer need to define every single token in the `tokens` block. You can use string literals directly in your rules!

```acanthophis
rule Statement:
    | "if" cond:Expr "then" body:Stmt -> If(cond, body)
    | "(" expr:Expr ")" -> expr
```
Acanthophis automatically generates the necessary tokens for you.

### 2. Flexible Quotes
Use single `'` or double `"` quotes for strings, just like in Python.

```acanthophis
rule String:
    | "double quoted" -> "ok"
    | 'single quoted' -> 'ok'
```

### 3. Semantic Checks & Error Reporting
You can now perform complex semantic checks directly in your grammar and report custom errors using the `error()` function.

```acanthophis
rule Age:
    | n:NUMBER -> int(n)
      check int(n) >= 18
      then pass
      else then error("Must be 18 or older")
```

### 4. Multiline Check Guards
Check guards can now span multiple lines for better readability.

```acanthophis
rule ComplexCheck:
    | val:Value -> val
      check val.is_valid() and
            val.has_permission()
      then process(val)
      else then error("Invalid value")
```

---

## 💻 Using the Generated Parser

Acanthophis generates a static, easy-to-use API.

```python
from Calculator_parser import Parser

# 1. Parse your text
result = Parser.parse("10 + 20 + 30")

# 2. Check if it worked
if result.is_valid:
    print("✅ Success!")
    print(f"AST: {result.ast}")
    # Output: Add(Add(Num(10), Num(20)), Num(30))
else:
    print(f"❌ Found {len(result.errors)} errors:")
    for error in result.errors:
        print(f" - {error.message} at line {error.line}")
```

### The `ParseResult` Object

The `Parser.parse()` method returns a typed object with everything you need:

| Field      | Type               | Description                                                |
| :--------- | :----------------- | :--------------------------------------------------------- |
| `is_valid` | `bool`             | `True` if parsing succeeded without errors.                |
| `ast`      | `Any`              | The generated Abstract Syntax Tree (or `None` on failure). |
| `errors`   | `List[ParseError]` | A list of all syntax errors found (thanks to recovery).    |
| `tokens`   | `List[Token]`      | The raw tokens produced by the lexer.                      |

---

## 🧰 CLI Reference

The `acanthophis` command is your swiss-army knife.

| Command | Description                                   | Example                      |
| :------ | :-------------------------------------------- | :--------------------------- |
| `init`  | Create a new grammar file with boilerplate.   | `acanthophis init MyLang`    |
| `build` | Compile `.apy` files to Python parsers.       | `acanthophis build lang.apy` |
| `check` | Validate grammar syntax (linter).             | `acanthophis check lang.apy` |
| `test`  | Run the tests defined inside the grammar.     | `acanthophis test lang.apy`  |
| `fmt`   | Auto-format your grammar file.                | `acanthophis fmt lang.apy`   |
| `repl`  | Start an interactive shell for your language. | `acanthophis repl lang.apy`  |

**Common Flags:**
*   `--no-recovery`: Disable error recovery generation (fail fast).
*   `-o DIR`: Specify output directory for generated files.
*   `-v`: Verbose mode.

---

## 📚 Language Cheat Sheet

### Tokens
Define regex patterns for your lexer. Order matters!

```acanthophis
tokens:
    IF: if              # Keywords first
    ID: [a-z]+          # Identifiers later
    WS: skip \s+        # 'skip' ignores this token in the AST
end
```

### Rules & Actions
Map syntax to AST nodes using `->`.

```acanthophis
rule Statement:
    # Match 'return' then an Expr. Bind Expr to 'e'.
    # Return a ReturnNode class with 'e' as argument.
    | RETURN e:Expr SEMI -> ReturnNode(e)
    
    # 'pass' returns the child value directly (no wrapper)
    | e:Expr SEMI -> pass
end
```

### Check Guards
Add semantic logic directly to your grammar.

```acanthophis
rule Byte:
    | n:NUMBER -> int(n) check int(n) < 256 then pass else then error("Value too large")
end
```

---

## 🔮 Advanced Features

### Left Recursion
Write grammars naturally. `Expr: Expr + Term` works out of the box. Acanthophis handles the complex logic behind the scenes so you don't have to rewrite your grammar into a confusing right-recursive mess.

### Error Recovery (Panic Mode)
Most parsers stop at the first error. Acanthophis parsers synchronize and keep going. This means your users get **all** the errors in their file at once, not just the first one.

---

## 📄 License

BSD Licence
