import sys
import json
import os
import logging
import re
import urllib.parse
import urllib.request
from linter.venom_linter import VenomLinter
from formatter.constrictor_formatter import ConstrictorFormatter

# Configure logging to stderr so it shows up in VS Code Output channel
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class AcanthoLanguageServer:
    def __init__(self):
        self.running = True
        self.documents = {}  # Map uri -> content

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

        linter = VenomLinter(file_path, content=content)
        diagnostics = linter.lint()

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

        try:
            formatter = ConstrictorFormatter(content)
            formatted = formatter.format()

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

    def provide_code_actions(self, msg_id, params):
        try:
            context = params.get("context", {})
            diagnostics = context.get("diagnostics", [])
            uri = params["textDocument"]["uri"]
            content = self.documents.get(uri, "")
            lines = content.split("\n")

            actions = []

            for diag in diagnostics:
                code = diag.get("code")
                if not code:
                    continue

                line_idx = diag["range"]["start"]["line"]
                line_content = ""
                if 0 <= line_idx < len(lines):
                    line_content = lines[line_idx]

                if code == "unused-token":
                    match = re.search(r"Token '(\w+)'", diag["message"])
                    if match:
                        token_name = match.group(1)
                        if ":" in line_content and "skip" not in line_content:
                            # Replace the whole line to insert 'skip' safely
                            parts = line_content.split(":", 1)
                            new_line = f"{parts[0]}: skip {parts[1].strip()}"
                            actions.append(
                                self._create_quickfix(
                                    f"Mark '{token_name}' as skip",
                                    uri,
                                    line_idx,
                                    new_line,
                                    diag,
                                )
                            )

                elif code == "naming-convention-token":
                    match = re.search(r"Token '(\w+)'", diag["message"])
                    if match:
                        token_name = match.group(1)
                        upper_name = token_name.upper()
                        # Find position of token_name in line
                        col = line_content.find(token_name)
                        if col != -1:
                            actions.append(
                                self._create_replace_edit(
                                    f"Rename to '{upper_name}'",
                                    uri,
                                    line_idx,
                                    col,
                                    col + len(token_name),
                                    upper_name,
                                    diag,
                                )
                            )

                elif code == "naming-convention-rule":
                    match = re.search(r"Rule '(\w+)'", diag["message"])
                    if match:
                        rule_name = match.group(1)
                        pascal_name = rule_name[0].upper() + rule_name[1:]
                        col = line_content.find(rule_name)
                        if col != -1:
                            actions.append(
                                self._create_replace_edit(
                                    f"Rename to '{pascal_name}'",
                                    uri,
                                    line_idx,
                                    col,
                                    col + len(rule_name),
                                    pascal_name,
                                    diag,
                                )
                            )

                elif code == "undefined-reference":
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

                    # Also offer to create the rule
                    undefined_match = re.search(
                        r"Undefined reference: '(\w+)'", diag["message"]
                    )
                    if undefined_match:
                        new_rule_name = undefined_match.group(1)
                        # Add at the end of file
                        last_line = len(lines)
                        new_text = f"\n\nrule {new_rule_name}:\n    # TODO: Implement rule\n    | 'literal'\nend"
                        actions.append(
                            {
                                "title": f"Create rule '{new_rule_name}'",
                                "kind": "quickfix",
                                "diagnostics": [diag],
                                "edit": {
                                    "changes": {
                                        uri: [
                                            {
                                                "range": {
                                                    "start": {
                                                        "line": last_line,
                                                        "character": 0,
                                                    },
                                                    "end": {
                                                        "line": last_line,
                                                        "character": 0,
                                                    },
                                                },
                                                "newText": new_text,
                                            }
                                        ]
                                    }
                                },
                            }
                        )

                elif code == "unreachable-rule":
                    # Delete the rule block
                    # Find 'end'
                    start_line = line_idx
                    end_line = start_line
                    for i in range(start_line, len(lines)):
                        if lines[i].strip() == "end":
                            end_line = i
                            break

                    actions.append(
                        {
                            "title": "Delete unreachable rule",
                            "kind": "quickfix",
                            "diagnostics": [diag],
                            "edit": {
                                "changes": {
                                    uri: [
                                        {
                                            "range": {
                                                "start": {
                                                    "line": start_line,
                                                    "character": 0,
                                                },
                                                "end": {
                                                    "line": end_line + 1,
                                                    "character": 0,
                                                },
                                            },
                                            "newText": "",
                                        }
                                    ]
                                }
                            },
                        }
                    )

                elif code == "token-shadowing":
                    # Message: Token 'name2' may be shadowed by earlier general token 'name1' (line 123).
                    match = re.search(
                        r"earlier general token '(\w+)' \(line (\d+)\)", diag["message"]
                    )
                    if match:
                        shadowing_token = match.group(1)
                        shadowing_line = int(match.group(2)) - 1  # 0-indexed

                        # Move current line (line_idx) to before shadowing_line
                        current_line_text = lines[line_idx] + "\n"

                        actions.append(
                            {
                                "title": f"Move before '{shadowing_token}'",
                                "kind": "quickfix",
                                "diagnostics": [diag],
                                "edit": {
                                    "changes": {
                                        uri: [
                                            # Delete current line
                                            {
                                                "range": {
                                                    "start": {
                                                        "line": line_idx,
                                                        "character": 0,
                                                    },
                                                    "end": {
                                                        "line": line_idx + 1,
                                                        "character": 0,
                                                    },
                                                },
                                                "newText": "",
                                            },
                                            # Insert before shadowing line
                                            {
                                                "range": {
                                                    "start": {
                                                        "line": shadowing_line,
                                                        "character": 0,
                                                    },
                                                    "end": {
                                                        "line": shadowing_line,
                                                        "character": 0,
                                                    },
                                                },
                                                "newText": current_line_text,
                                            },
                                        ]
                                    }
                                },
                            }
                        )

                elif code == "missing-grammar-name":
                    actions.append(
                        {
                            "title": "Add 'grammar Name:'",
                            "kind": "quickfix",
                            "diagnostics": [diag],
                            "edit": {
                                "changes": {
                                    uri: [
                                        {
                                            "range": {
                                                "start": {"line": 0, "character": 0},
                                                "end": {"line": 0, "character": 0},
                                            },
                                            "newText": "grammar MyGrammar:\n\n",
                                        }
                                    ]
                                }
                            },
                        }
                    )

                elif code == "missing-tokens-block":
                    insert_line = 0
                    match = re.search(r"grammar\s+\w+:", content)
                    if match:
                        insert_line = content.count("\n", 0, match.end()) + 1

                    actions.append(
                        {
                            "title": "Add 'tokens:' block",
                            "kind": "quickfix",
                            "diagnostics": [diag],
                            "edit": {
                                "changes": {
                                    uri: [
                                        {
                                            "range": {
                                                "start": {
                                                    "line": insert_line,
                                                    "character": 0,
                                                },
                                                "end": {
                                                    "line": insert_line,
                                                    "character": 0,
                                                },
                                            },
                                            "newText": "tokens:\n    # Define tokens here\nend\n\n",
                                        }
                                    ]
                                }
                            },
                        }
                    )

                elif code == "rule-missing-tests":
                    match = re.search(r"Rule '(\w+)'", diag["message"])
                    if match:
                        rule_name = match.group(1)
                        # Find the end of the rule
                        insert_line = line_idx + 1
                        for i in range(line_idx, len(lines)):
                            if lines[i].strip() == "end":
                                insert_line = i + 1
                                break

                        new_text = f'\ntest {rule_name}Tests {rule_name}:\n    "input" => Result\nend\n'
                        actions.append(
                            {
                                "title": f"Add tests for '{rule_name}'",
                                "kind": "quickfix",
                                "diagnostics": [diag],
                                "edit": {
                                    "changes": {
                                        uri: [
                                            {
                                                "range": {
                                                    "start": {
                                                        "line": insert_line,
                                                        "character": 0,
                                                    },
                                                    "end": {
                                                        "line": insert_line,
                                                        "character": 0,
                                                    },
                                                },
                                                "newText": new_text,
                                            }
                                        ]
                                    }
                                },
                            }
                        )
                elif code == "naming-convention-token":
                    match = re.search(r"Token '(\w+)'", diag["message"])
                    if match:
                        token_name = match.group(1)
                        upper_name = token_name.upper()

                        edits = []
                        for i, line in enumerate(lines):
                            for m in re.finditer(
                                r"\b" + re.escape(token_name) + r"\b", line
                            ):
                                edits.append(
                                    {
                                        "range": {
                                            "start": {
                                                "line": i,
                                                "character": m.start(),
                                            },
                                            "end": {"line": i, "character": m.end()},
                                        },
                                        "newText": upper_name,
                                    }
                                )

                        actions.append(
                            {
                                "title": f"Convert '{token_name}' to UPPERCASE",
                                "kind": "quickfix",
                                "diagnostics": [diag],
                                "edit": {"changes": {uri: edits}},
                            }
                        )

            # Check for Fix All opportunity
            lowercase_tokens = set()
            for diag in diagnostics:
                if diag.get("code") == "naming-convention-token":
                    match = re.search(r"Token '(\w+)'", diag["message"])
                    if match:
                        lowercase_tokens.add(match.group(1))

            if lowercase_tokens:
                all_edits = []
                for token_name in lowercase_tokens:
                    upper_name = token_name.upper()
                    for i, line in enumerate(lines):
                        for m in re.finditer(
                            r"\b" + re.escape(token_name) + r"\b", line
                        ):
                            all_edits.append(
                                {
                                    "range": {
                                        "start": {"line": i, "character": m.start()},
                                        "end": {"line": i, "character": m.end()},
                                    },
                                    "newText": upper_name,
                                }
                            )

                actions.append(
                    {
                        "title": "Fix all lowercase tokens",
                        "kind": "source.fixAll",
                        "edit": {"changes": {uri: all_edits}},
                    }
                )

            self.send_response(msg_id, actions)

        except Exception as e:
            logging.error(f"Code Action error: {e}")
            self.send_error(msg_id, -32603, str(e))

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
