# Acanthophis Language Extension for VS Code

This extension provides syntax highlighting and comprehensive linting for Acanthophis (.apy) grammar files.

## Features

### Syntax Highlighting
- Full syntax highlighting for `.apy` files
- Recognizes grammar definitions, tokens, rules, and test blocks

### Venom Linter
The extension includes **Venom Linter**, a powerful static analysis tool that checks your grammar files for common issues and best practices.

#### Linter Checks

**Essential Checks:**
- **Undefined References**: Detects rules or tokens used but not defined, with smart suggestions using Levenshtein distance ("Did you mean 'Addition'?")
- **Unreachable Rules**: Identifies "orphan" rules that cannot be reached from the start rule
- **Left Recursion**: Detects direct left recursion which is not supported by PEG parsers
- **Missing Structure**: Checks for missing `grammar Name:` or `tokens:` blocks
- **Duplicate Definitions**: Warns if tokens are defined multiple times
- **Regex Validity**: Validates that token regex patterns are valid Python regular expressions

**DX Improvements:**
- **Naming Conventions**: Enforces `UPPERCASE` for tokens and `PascalCase` for rules
- **Token Shadowing**: Warns when more general token patterns shadow specific ones (e.g., identifier pattern before keywords)
- **Unused Tokens**: Detects tokens not marked as `skip` and not used in any rule
- **AST Constructor Consistency**: Validates that AST nodes are constructed with consistent arguments across the grammar
- **Test Coverage**: Reports rules without associated test cases
- **Unnecessary Captures**: Suggests removing capture labels when using `-> pass` with multiple captures

## Requirements

- Python 3.8+ must be installed and available in PATH
- VS Code 1.0.0 or higher

## Installation

1. Copy the `acantho-lang` folder to your VS Code extensions directory:
   - Windows: `%USERPROFILE%\.vscode\extensions\`
   - macOS/Linux: `~/.vscode/extensions/`

2. Reload VS Code

3. Open any `.apy` file to activate the extension

## Usage

The linter runs automatically when you:
- Open an `.apy` file
- Save an `.apy` file
- Type in the editor (live validation)

### Formatting
The extension includes **Constrictor Formatter**.
- Use `Shift + Alt + F` (or your configured shortcut) to format the document.
- The formatter aligns blocks, standardizes indentation, and cleans up spacing.

### Quick Fixes
The extension provides Quick Fixes (Code Actions) for common issues:
- **Unused Tokens**: Mark as `skip`
- **Naming Conventions**: Rename tokens to UPPERCASE (definition only)

### Commands
- `Acantho: Restart Language Server`: Restarts the language server, linter, and formatter without reloading the window.

## Troubleshooting

If the extension is not working:
1. Ensure Python is in your PATH.
2. Check the "Acantho Language Server" output channel in VS Code for logs.
3. Try restarting the server using the command palette.
- Save an `.apy` file

Diagnostics appear in:
- The Problems panel (View → Problems)
- Inline in the editor with squiggly underlines

### Severity Levels

- 🔴 **Error**: Critical issues that will cause parsing to fail
- 🟡 **Warning**: Potential issues that may cause unexpected behavior
- 🔵 **Information**: Suggestions for improving code quality and maintainability

## Extension Settings

Currently, the extension uses the default Python installation. Future versions may include:
- Custom Python interpreter path
- Configurable linter rules
- Auto-fix capabilities

## Known Issues

None at this time. Please report issues to the project repository.

## Release Notes

### 0.0.2
- Added Venom Linter with comprehensive static analysis
- Token shadowing detection
- Smart error suggestions with Levenshtein distance
- AST constructor consistency checking
- Test coverage analysis
- Unused token detection
- Unnecessary capture detection

### 0.0.1
- Initial release
- Basic syntax highlighting for `.apy` files

## Contributing

Contributions are welcome! Please submit issues and pull requests to the project repository.

## License

MIT
