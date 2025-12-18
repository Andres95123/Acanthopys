import sys
import os
import pytest

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import AcanthoLanguageServer


class TestServer:
    def setup_method(self):
        self.server = AcanthoLanguageServer()

    def test_rename_logic(self):
        # Mock document content
        uri = "file://test.apy"
        content = """
grammar Test:
    rule A:
        'a'
    end
    
    rule B:
        A
    end
end
"""
        self.server.documents[uri] = content

        # Simulate rename request for 'A' at line 2 (rule A:)
        # Line 0: ""
        # Line 1: "grammar Test:"
        # Line 2: "    rule A:" -> 'A' starts at index 9

        params = {
            "textDocument": {"uri": uri},
            "position": {"line": 2, "character": 9},
            "newName": "NewRule",
        }

        # We need to intercept send_response to check result
        response = None

        def mock_send_response(mid, res):
            nonlocal response
            response = res

        self.server.send_response = mock_send_response

        self.server.handle_rename(1, params)

        assert response is not None
        changes = response["changes"][uri]

        # Should find 2 occurrences: definition of A and usage of A
        assert len(changes) == 2

        # Check if newText is correct
        assert changes[0]["newText"] == "NewRule"
        assert changes[1]["newText"] == "NewRule"

    def test_code_action_rename_all(self):
        uri = "file://test.apy"
        content = "grammar Test:\n    rule A:\n        'a'\n    end\nend"
        self.server.documents[uri] = content

        # Cursor on 'A'
        params = {
            "textDocument": {"uri": uri},
            "range": {
                "start": {"line": 1, "character": 9},
                "end": {"line": 1, "character": 10},
            },
            "context": {"diagnostics": []},
        }

        response = None

        def mock_send_response(mid, res):
            nonlocal response
            response = res

        self.server.send_response = mock_send_response

        self.server.provide_code_actions(1, params)

        assert response is not None
        # Look for refactor.rename
        rename_action = next(
            (a for a in response if a["kind"] == "refactor.rename"), None
        )
        assert rename_action is not None
        assert rename_action["title"] == "Rename Symbol"

    def test_code_action_extract_rule(self):
        uri = "file://test.apy"
        content = "grammar Test:\n    rule A:\n        'literal'\n    end\nend"
        self.server.documents[uri] = content

        # Select 'literal'
        params = {
            "textDocument": {"uri": uri},
            "range": {
                "start": {"line": 2, "character": 8},
                "end": {"line": 2, "character": 17},
            },
            "context": {"diagnostics": []},
        }

        response = None

        def mock_send_response(mid, res):
            nonlocal response
            response = res

        self.server.send_response = mock_send_response

        self.server.provide_code_actions(1, params)

        assert response is not None
        extract_action = next(
            (a for a in response if a["kind"] == "refactor.extract"), None
        )
        assert extract_action is not None
        assert "Extract to rule" in extract_action["title"]

        changes = extract_action["edit"]["changes"][uri]
        assert len(changes) == 2
        # One change to add the rule, one to replace the literal
        assert any("rule NewRule" in c["newText"] for c in changes)
        assert any("NewRule" == c["newText"] for c in changes)

    def test_code_action_shadowing(self):
        uri = "file://test.apy"
        content = (
            "grammar Test:\n    tokens:\n        t1: 'a'\n        t2: 'b'\n    end\nend"
        )
        self.server.documents[uri] = content

        # Diagnostic for shadowing
        # t1 is at line 2 (0-indexed)
        # t2 is at line 3 (0-indexed)
        # Message says t1 (line 3, 1-based) shadows t2
        diag = {
            "range": {
                "start": {"line": 3, "character": 8},
                "end": {"line": 3, "character": 10},
            },
            "message": "Token 't2' may be shadowed by earlier token 't1'. Token 't1' (line 3) has a more general pattern that matches 't2'.",
            "code": "token-shadowing",
        }

        params = {"textDocument": {"uri": uri}, "context": {"diagnostics": [diag]}}

        response = None

        def mock_send_response(mid, res):
            nonlocal response
            response = res

        self.server.send_response = mock_send_response

        self.server.provide_code_actions(1, params)

        assert response is not None
        shadow_action = next((a for a in response if "Move before" in a["title"]), None)
        assert shadow_action is not None

        changes = shadow_action["edit"]["changes"][uri]
        assert len(changes) == 2

        # Check insertion point
        # Should insert at line 2 (before t1)
        insertion = next(c for c in changes if c["newText"] != "")
        assert insertion["range"]["start"]["line"] == 2

        # Check deletion point
        # Should delete line 3 (t2)
        deletion = next(c for c in changes if c["newText"] == "")
        assert deletion["range"]["start"]["line"] == 3

    def test_code_action_extract_token(self):
        uri = "file://test.apy"
        content = "grammar Test:\n    tokens:\n    end\n    rule A:\n        'literal'\n    end\nend"
        self.server.documents[uri] = content

        # Select 'literal'
        params = {
            "textDocument": {"uri": uri},
            "range": {
                "start": {"line": 4, "character": 8},
                "end": {"line": 4, "character": 17},
            },
            "context": {"diagnostics": []},
        }

        response = None

        def mock_send_response(mid, res):
            nonlocal response
            response = res

        self.server.send_response = mock_send_response

        self.server.provide_code_actions(1, params)

        assert response is not None
        extract_token = next(
            (a for a in response if "Extract to token" in a["title"]), None
        )
        assert extract_token is not None

        changes = extract_token["edit"]["changes"][uri]
        assert len(changes) == 2
        # One change to add the token, one to replace the literal
        assert any("NEW_TOKEN" in c["newText"] for c in changes)
        # Check insertion in tokens block (line 2 is 'end')
        insertion = next(c for c in changes if "NEW_TOKEN:" in c["newText"])
        assert insertion["range"]["start"]["line"] == 2

    def test_code_action_fix_all(self):
        uri = "file://test.apy"
        content = "grammar Test:\n    rule a:\n        'literal'\n    end\n    rule b:\n        'other'\n    end\nend"
        self.server.documents[uri] = content

        # Simulate diagnostics for lowercase rules
        diagnostics = [
            {
                "range": {
                    "start": {"line": 1, "character": 9},
                    "end": {"line": 1, "character": 10},
                },
                "message": "Rule 'a' should be PascalCase",
                "code": "naming-convention-rule",
                "source": "venom-linter",
            },
            {
                "range": {
                    "start": {"line": 4, "character": 9},
                    "end": {"line": 4, "character": 10},
                },
                "message": "Rule 'b' should be PascalCase",
                "code": "naming-convention-rule",
                "source": "venom-linter",
            },
        ]

        params = {
            "textDocument": {"uri": uri},
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 0},
            },
            "context": {"diagnostics": diagnostics, "only": ["source.fixAll"]},
        }

        response = None

        def mock_send_response(mid, res):
            nonlocal response
            response = res

        self.server.send_response = mock_send_response
        self.server.provide_code_actions(1, params)

        assert response is not None
        fix_all_action = next(
            (a for a in response if a["kind"] == "source.fixAll"), None
        )
        assert fix_all_action is not None
        assert fix_all_action["title"] == "Fix all issues"

        changes = fix_all_action["edit"]["changes"][uri]
        # Should have edits for both 'a' -> 'A' and 'b' -> 'B'
        # Note: calculate_rename_edits might return multiple edits per rename if the symbol is used elsewhere
        # But here we just define them.

        new_texts = [c["newText"] for c in changes]
        assert "A" in new_texts
        assert "B" in new_texts
