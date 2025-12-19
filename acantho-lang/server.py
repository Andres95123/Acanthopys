import sys
import json
import os
import logging
import re
import urllib.parse
import urllib.request
import subprocess
import tempfile

# Configure logging to stderr so it shows up in VS Code Output channel
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class AcanthoLanguageServer:
    def __init__(self):
        self.running = True
        self.documents = {}  # Map uri -> content

        # Locate acanthophis executable
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.executable = os.path.join(base_dir, "bin", "acanthophis.exe")
        if not os.path.exists(self.executable):
            # Fallback for development/testing if not in bin
            self.executable = "acanthophis"

    def run(self):
        logging.info("Acantho Language Server started")
        while self.running:
            try:
                # Read headers
                content_length = 0
                while True:
                    header = sys.stdin.buffer.readline().decode("utf-8")
                    if not header:
                        # EOF
                        self.running = False
                        break

                    header = header.strip()
                    if not header:
                        # Empty line marks end of headers
                        break

                    if header.startswith("Content-Length:"):
                        content_length = int(header.split(":")[1].strip())

                if not self.running:
                    break

                if content_length > 0:
                    content = sys.stdin.buffer.read(content_length).decode("utf-8")
                    request = json.loads(content)
                    self.handle_request(request)
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                break

    def handle_request(self, request):
        method = request.get("method")
        params = request.get("params")
        msg_id = request.get("id")

        logging.info(f"Handling request: {method}")

        if method == "initialize":
            self.send_response(
                msg_id,
                {
                    "capabilities": {
                        "textDocumentSync": 1,  # Full sync
                        "documentFormattingProvider": True,
                        "codeActionProvider": True,
                        "renameProvider": True,
                    }
                },
            )

        elif method == "textDocument/didOpen":
            uri = params["textDocument"]["uri"]
            text = params["textDocument"]["text"]
            self.documents[uri] = text
            self.validate_document(uri)

        elif method == "textDocument/didSave":
            uri = params["textDocument"]["uri"]
            self.validate_document(uri)

        elif method == "textDocument/didChange":
            uri = params["textDocument"]["uri"]
            if params.get("contentChanges"):
                self.documents[uri] = params["contentChanges"][-1]["text"]
            self.validate_document(uri)

        elif method == "textDocument/formatting":
            self.format_document(msg_id, params)

        elif method == "textDocument/codeAction":
            self.provide_code_actions(msg_id, params)

        elif method == "textDocument/rename":
            self.handle_rename(msg_id, params)

        elif method == "shutdown":
            self.send_response(msg_id, None)

        elif method == "exit":
            self.running = False

    def validate_document(self, uri):
        file_path = self._uri_to_path(uri)
        content = self.documents.get(uri)

        if content is None:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.documents[uri] = content
            except Exception as e:
                logging.error(f"Failed to read file {file_path}: {e}")
                return

        logging.info(f"Validating {file_path}")

        # Create temp file with content
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".apy", encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Run linter
            result = subprocess.run(
                [self.executable, "lint", tmp_path, "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            if result.returncode != 0 and not result.stdout:
                logging.error(f"Linter failed: {result.stderr}")
                return

            try:
                diagnostics = json.loads(result.stdout)
            except json.JSONDecodeError:
                logging.error(f"Failed to parse linter output: {result.stdout}")
                return

            lsp_diagnostics = []
            for diag in diagnostics:
                severity = 1  # Error
                if diag["severity"] == "Warning":
                    severity = 2
                elif diag["severity"] == "Information":
                    severity = 3

                d = {
                    "range": {
                        "start": {"line": diag["line"] - 1, "character": 0},
                        "end": {"line": diag["line"] - 1, "character": 1000},
                    },
                    "severity": severity,
                    "message": diag["message"],
                    "source": "Venom",
                }
                if "code" in diag:
                    d["code"] = diag["code"]

                lsp_diagnostics.append(d)

            self.send_notification(
                "textDocument/publishDiagnostics",
                {"uri": uri, "diagnostics": lsp_diagnostics},
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def format_document(self, msg_id, params):
        uri = params["textDocument"]["uri"]
        content = self.documents.get(uri)

        if content is None:
            file_path = self._uri_to_path(uri)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                self.send_error(msg_id, -32603, str(e))
                return

        # Create temp file with content
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".apy", encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Run formatter
            result = subprocess.run(
                [self.executable, "format", tmp_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            if result.returncode != 0:
                logging.error(f"Formatter failed: {result.stderr}")
                self.send_error(msg_id, -32603, f"Formatter failed: {result.stderr}")
                return

            formatted = result.stdout

            lines = content.split("\n")
            end_line = len(lines)
            end_char = len(lines[-1]) if lines else 0

            edit = {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": end_line, "character": end_char},
                },
                "newText": formatted,
            }

            self.send_response(msg_id, [edit])

        except Exception as e:
            logging.error(f"Formatting error: {e}")
            self.send_error(msg_id, -32603, str(e))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def calculate_rename_edits(self, uri, old_name, new_name):
        content = self.documents.get(uri, "")
        lines = content.split("\n")
        edits = []

        # Iterate over all lines to find matches
        # We use regex with word boundaries \b to ensure we match whole words
        for i, l in enumerate(lines):
            for match in re.finditer(r"\b" + re.escape(old_name) + r"\b", l):
                edits.append(
                    {
                        "range": {
                            "start": {"line": i, "character": match.start()},
                            "end": {"line": i, "character": match.end()},
                        },
                        "newText": new_name,
                    }
                )
        return edits

    def handle_rename(self, msg_id, params):
        try:
            uri = params["textDocument"]["uri"]
            position = params["position"]
            new_name = params["newName"]
            content = self.documents.get(uri, "")

            # 1. Identify the symbol at the position
            lines = content.split("\n")
            line_idx = position["line"]
            char_idx = position["character"]

            if line_idx >= len(lines):
                self.send_response(msg_id, None)
                return

            line = lines[line_idx]

            # Simple regex to find word at position
            # This is a naive implementation. A proper one would use the parser's location info.
            # But since we have the content, we can try to find the word boundaries.

            # Find start of word
            start = char_idx
            while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
                start -= 1

            # Find end of word
            end = char_idx
            while end < len(line) and (line[end].isalnum() or line[end] == "_"):
                end += 1

            if start == end:
                # No word found
                self.send_response(msg_id, None)
                return

            old_name = line[start:end]
            logging.info(f"Renaming '{old_name}' to '{new_name}'")

            # 2. Find all occurrences
            edits = self.calculate_rename_edits(uri, old_name, new_name)

            workspace_edit = {"changes": {uri: edits}}

            self.send_response(msg_id, workspace_edit)

        except Exception as e:
            logging.error(f"Rename error: {e}")
            self.send_error(msg_id, -32603, str(e))

    def provide_code_actions(self, msg_id, params):
        try:
            context = params.get("context", {})
            diagnostics = context.get("diagnostics", [])
            uri = params["textDocument"]["uri"]

            actions = []

            # 1. Quick Fixes (Diagnostic-based)
            actions.extend(self._get_quick_fixes(uri, diagnostics))

            # 2. Refactorings (Selection-based)
            actions.extend(self._get_refactorings(uri, params.get("range")))

            # 3. Source Actions (Fix All)
            if context.get("only") and "source.fixAll" in context["only"]:
                actions.extend(self._get_fix_all_actions(uri, diagnostics))
            elif not context.get("only"):
                # Also offer fix all if no specific kind requested (VS Code behavior varies)
                actions.extend(self._get_fix_all_actions(uri, diagnostics))

            self.send_response(msg_id, actions)

        except Exception as e:
            logging.error(f"CodeAction error: {e}")
            self.send_error(msg_id, -32603, str(e))

    def _get_quick_fixes(self, uri, diagnostics):
        actions = []
        for diag in diagnostics:
            code = diag.get("code")
            if not code:
                continue

            handler_name = f"_fix_{code.replace('-', '_')}"
            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                try:
                    fix = handler(uri, diag)
                    if fix:
                        if isinstance(fix, list):
                            actions.extend(fix)
                        else:
                            actions.append(fix)
                except Exception as e:
                    logging.error(f"Error in quick fix handler {handler_name}: {e}")
        return actions

    def _get_refactorings(self, uri, rng):
        actions = []
        if not rng:
            return actions

        start_line = rng["start"]["line"]
        start_char = rng["start"]["character"]
        end_line = rng["end"]["line"]
        end_char = rng["end"]["character"]

        line_content = self._get_line(uri, start_line)
        if not line_content:
            return actions

        # Rename Symbol
        word_match = None
        for m in re.finditer(r"\w+", line_content):
            if m.start() <= start_char <= m.end():
                word_match = m
                break

        if word_match:
            actions.append(
                {
                    "title": "Rename Symbol",
                    "kind": "refactor.rename",
                    "command": {
                        "title": "Rename Symbol",
                        "command": "editor.action.rename",
                    },
                }
            )

        # Extract Rule / Token
        if start_line == end_line and start_char < end_char:
            selected_text = line_content[start_char:end_char]
            if (selected_text.startswith("'") and selected_text.endswith("'")) or (
                selected_text.startswith('"') and selected_text.endswith('"')
            ):
                # Extract Rule
                new_rule_name = "NewRule"
                content = self.documents.get(uri, "")
                lines = content.split("\n")
                last_line = len(lines)
                new_rule_text = f"\n\nrule {new_rule_name}:\n    {selected_text}\nend"

                actions.append(
                    self._create_workspace_edit(
                        f"Extract to rule '{new_rule_name}'",
                        uri,
                        [
                            {
                                "range": {
                                    "start": {"line": last_line, "character": 0},
                                    "end": {"line": last_line, "character": 0},
                                },
                                "newText": new_rule_text,
                            },
                            {"range": rng, "newText": new_rule_name},
                        ],
                        kind="refactor.extract",
                    )
                )

                # Extract Token
                tokens_start = -1
                tokens_end = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith("tokens:"):
                        tokens_start = i
                    if tokens_start != -1 and line.strip() == "end":
                        tokens_end = i
                        break

                if tokens_start != -1 and tokens_end != -1:
                    new_token_name = "NEW_TOKEN"
                    token_def = f"        {new_token_name}: {selected_text}\n"

                    actions.append(
                        self._create_workspace_edit(
                            f"Extract to token '{new_token_name}'",
                            uri,
                            [
                                {
                                    "range": {
                                        "start": {"line": tokens_end, "character": 0},
                                        "end": {"line": tokens_end, "character": 0},
                                    },
                                    "newText": token_def,
                                },
                                {"range": rng, "newText": new_token_name},
                            ],
                            kind="refactor.extract",
                        )
                    )
        return actions

    def _get_fix_all_actions(self, uri, diagnostics):
        actions = []
        edits = []

        # Collect all safe edits
        for diag in diagnostics:
            code = diag.get("code")
            if code == "naming-convention-token":
                match = re.search(r"Token '(\w+)'", diag["message"])
                if match:
                    token_name = match.group(1)
                    upper_name = token_name.upper()
                    edits.extend(
                        self.calculate_rename_edits(uri, token_name, upper_name)
                    )

            elif code == "naming-convention-rule":
                match = re.search(r"Rule '(\w+)'", diag["message"])
                if match:
                    rule_name = match.group(1)
                    pascal_name = rule_name[0].upper() + rule_name[1:]
                    edits.extend(
                        self.calculate_rename_edits(uri, rule_name, pascal_name)
                    )

            elif code == "missing-grammar-name":
                edits.append(
                    {
                        "range": {
                            "start": {"line": 0, "character": 0},
                            "end": {"line": 0, "character": 0},
                        },
                        "newText": "grammar MyGrammar:\n\n",
                    }
                )

            elif code == "missing-tokens-block":
                content = self.documents.get(uri, "")
                insert_line = 0
                match = re.search(r"grammar\s+\w+:", content)
                if match:
                    insert_line = content.count("\n", 0, match.end()) + 1
                edits.append(
                    {
                        "range": {
                            "start": {"line": insert_line, "character": 0},
                            "end": {"line": insert_line, "character": 0},
                        },
                        "newText": "    tokens:\n        # Define tokens here\n    end\n\n",
                    }
                )

            elif code == "unused-token":
                line_idx = diag["range"]["start"]["line"]
                edits.append(
                    {
                        "range": {
                            "start": {"line": line_idx, "character": 0},
                            "end": {"line": line_idx + 1, "character": 0},
                        },
                        "newText": "",
                    }
                )

        if edits:
            # Deduplicate edits based on range and newText
            unique_edits = []
            seen = set()
            for edit in edits:
                key = (
                    edit["range"]["start"]["line"],
                    edit["range"]["start"]["character"],
                    edit["range"]["end"]["line"],
                    edit["range"]["end"]["character"],
                    edit["newText"],
                )
                if key not in seen:
                    seen.add(key)
                    unique_edits.append(edit)

            actions.append(
                self._create_workspace_edit(
                    "Fix all issues", uri, unique_edits, kind="source.fixAll"
                )
            )

        return actions

    # --- Quick Fix Handlers ---

    def _fix_naming_convention_token(self, uri, diag):
        match = re.search(r"Token '(\w+)'", diag["message"])
        if match:
            token_name = match.group(1)
            upper_name = token_name.upper()
            edits = self.calculate_rename_edits(uri, token_name, upper_name)
            return self._create_workspace_edit(
                f"Rename '{token_name}' to '{upper_name}'",
                uri,
                edits,
                diagnostics=[diag],
            )

    def _fix_naming_convention_rule(self, uri, diag):
        match = re.search(r"Rule '(\w+)'", diag["message"])
        if match:
            rule_name = match.group(1)
            pascal_name = rule_name[0].upper() + rule_name[1:]
            edits = self.calculate_rename_edits(uri, rule_name, pascal_name)
            return self._create_workspace_edit(
                f"Rename '{rule_name}' to '{pascal_name}'",
                uri,
                edits,
                diagnostics=[diag],
            )

    def _fix_undefined_reference(self, uri, diag):
        actions = []
        line_idx = diag["range"]["start"]["line"]
        line_content = self._get_line(uri, line_idx)

        # Suggestion
        match = re.search(r"Did you mean '(\w+)'\?", diag["message"])
        if match:
            suggestion = match.group(1)
            undefined_match = re.search(
                r"Undefined reference: '(\w+)'", diag["message"]
            )
            if undefined_match:
                undefined_word = undefined_match.group(1)
                col = line_content.find(undefined_word)
                if col != -1:
                    actions.append(
                        self._create_replace_edit(
                            f"Change to '{suggestion}'",
                            uri,
                            line_idx,
                            col,
                            col + len(undefined_word),
                            suggestion,
                            diag,
                        )
                    )

        # Create Rule
        undefined_match = re.search(r"Undefined reference: '(\w+)'", diag["message"])
        if undefined_match:
            new_rule_name = undefined_match.group(1)
            content = self.documents.get(uri, "")
            lines = content.split("\n")
            last_line = len(lines)
            new_text = f"\n\nrule {new_rule_name}:\n    # TODO: Implement rule\n    | 'literal'\nend"
            actions.append(
                self._create_workspace_edit(
                    f"Create rule '{new_rule_name}'",
                    uri,
                    [
                        {
                            "range": {
                                "start": {"line": last_line, "character": 0},
                                "end": {"line": last_line, "character": 0},
                            },
                            "newText": new_text,
                        }
                    ],
                    diagnostics=[diag],
                )
            )
        return actions

    def _fix_unreachable_rule(self, uri, diag):
        line_idx = diag["range"]["start"]["line"]
        content = self.documents.get(uri, "")
        lines = content.split("\n")
        start_line = line_idx
        end_line = start_line
        for i in range(start_line, len(lines)):
            if lines[i].strip() == "end":
                end_line = i
                break
        return self._create_workspace_edit(
            "Delete unreachable rule",
            uri,
            [
                {
                    "range": {
                        "start": {"line": start_line, "character": 0},
                        "end": {"line": end_line + 1, "character": 0},
                    },
                    "newText": "",
                }
            ],
            diagnostics=[diag],
        )

    def _fix_token_shadowing(self, uri, diag):
        match = re.search(
            r"Token '(\w+)' \(line (\d+)\) has a more general pattern", diag["message"]
        )
        if match:
            shadowing_token = match.group(1)
            shadowing_line = int(match.group(2)) - 1
            line_idx = diag["range"]["start"]["line"]
            line_content = self._get_line(uri, line_idx)
            current_line_text = line_content + "\n"

            return self._create_workspace_edit(
                f"Move before '{shadowing_token}' (Fix shadowing)",
                uri,
                [
                    {
                        "range": {
                            "start": {"line": shadowing_line, "character": 0},
                            "end": {"line": shadowing_line, "character": 0},
                        },
                        "newText": current_line_text,
                    },
                    {
                        "range": {
                            "start": {"line": line_idx, "character": 0},
                            "end": {"line": line_idx + 1, "character": 0},
                        },
                        "newText": "",
                    },
                ],
                diagnostics=[diag],
            )

    def _fix_missing_grammar_name(self, uri, diag):
        return self._create_workspace_edit(
            "Add 'grammar Name:'",
            uri,
            [
                {
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 0},
                    },
                    "newText": "grammar MyGrammar:\n\n",
                }
            ],
            diagnostics=[diag],
        )

    def _fix_missing_tokens_block(self, uri, diag):
        content = self.documents.get(uri, "")
        insert_line = 0
        match = re.search(r"grammar\s+\w+:", content)
        if match:
            insert_line = content.count("\n", 0, match.end()) + 1
        return self._create_workspace_edit(
            "Add 'tokens:' block",
            uri,
            [
                {
                    "range": {
                        "start": {"line": insert_line, "character": 0},
                        "end": {"line": insert_line, "character": 0},
                    },
                    "newText": "    tokens:\n        # Define tokens here\n    end\n\n",
                }
            ],
            diagnostics=[diag],
        )

    def _fix_rule_missing_tests(self, uri, diag):
        match = re.search(r"Rule '(\w+)'", diag["message"])
        if match:
            rule_name = match.group(1)
            line_idx = diag["range"]["start"]["line"]
            content = self.documents.get(uri, "")
            lines = content.split("\n")
            insert_line = line_idx + 1
            for i in range(line_idx, len(lines)):
                if lines[i].strip() == "end":
                    insert_line = i + 1
                    break
            new_text = (
                f'\ntest {rule_name}Tests {rule_name}:\n    "input" => Result\nend\n'
            )
            return self._create_workspace_edit(
                f"Add tests for '{rule_name}'",
                uri,
                [
                    {
                        "range": {
                            "start": {"line": insert_line, "character": 0},
                            "end": {"line": insert_line, "character": 0},
                        },
                        "newText": new_text,
                    }
                ],
                diagnostics=[diag],
            )

    def _fix_unused_token(self, uri, diag):
        line_idx = diag["range"]["start"]["line"]
        return self._create_workspace_edit(
            "Remove unused token",
            uri,
            [
                {
                    "range": {
                        "start": {"line": line_idx, "character": 0},
                        "end": {"line": line_idx + 1, "character": 0},
                    },
                    "newText": "",
                }
            ],
            diagnostics=[diag],
        )

    def _get_line(self, uri, line_idx):
        content = self.documents.get(uri, "")
        lines = content.split("\n")
        if 0 <= line_idx < len(lines):
            return lines[line_idx]
        return None

    def _create_workspace_edit(
        self, title, uri, edits, kind="quickfix", diagnostics=None
    ):
        action = {"title": title, "kind": kind, "edit": {"changes": {uri: edits}}}
        if diagnostics:
            action["diagnostics"] = diagnostics
        return action

    def _create_quickfix(self, title, uri, line_idx, new_text, diagnostic):
        # Replaces the entire line content (excluding newline)
        content = self.documents.get(uri, "")
        lines = content.split("\n")
        if not (0 <= line_idx < len(lines)):
            return None

        original_line = lines[line_idx]

        return {
            "title": title,
            "kind": "quickfix",
            "diagnostics": [diagnostic],
            "edit": {
                "changes": {
                    uri: [
                        {
                            "range": {
                                "start": {"line": line_idx, "character": 0},
                                "end": {
                                    "line": line_idx,
                                    "character": len(original_line),
                                },
                            },
                            "newText": new_text,
                        }
                    ]
                }
            },
        }

    def _create_replace_edit(
        self, title, uri, line_idx, start_col, end_col, new_text, diagnostic
    ):
        return {
            "title": title,
            "kind": "quickfix",
            "diagnostics": [diagnostic],
            "edit": {
                "changes": {
                    uri: [
                        {
                            "range": {
                                "start": {"line": line_idx, "character": start_col},
                                "end": {"line": line_idx, "character": end_col},
                            },
                            "newText": new_text,
                        }
                    ]
                }
            },
        }

    def _uri_to_path(self, uri):
        parsed = urllib.parse.urlparse(uri)
        path = urllib.request.url2pathname(parsed.path)
        # Remove leading backslash if it precedes a drive letter on Windows (e.g. \c:\...)
        if (
            os.name == "nt"
            and path.startswith("\\")
            and len(path) > 2
            and path[2] == ":"
        ):
            path = path[1:]
        return path

    def send_response(self, msg_id, result):
        response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
        self.send_message(response)

    def send_error(self, msg_id, code, message):
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message},
        }
        self.send_message(response)

    def send_notification(self, method, params):
        notification = {"jsonrpc": "2.0", "method": method, "params": params}
        self.send_message(notification)

    def send_message(self, msg):
        content = json.dumps(msg)
        content_bytes = content.encode("utf-8")
        header = f"Content-Length: {len(content_bytes)}\r\n\r\n"
        sys.stdout.buffer.write(header.encode("utf-8"))
        sys.stdout.buffer.write(content_bytes)
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    server = AcanthoLanguageServer()
    server.run()
