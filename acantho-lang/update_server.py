import re

file_path = r"c:\Users\andre\Desktop\Proyectos\Acanthopys\acantho-lang\server.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Define the start of the method to replace
start_marker = "    def provide_code_actions(self, msg_id, params):"
# Define the start of the next method
end_marker = "    def _get_line(self, uri, line_idx):"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find markers")
    exit(1)

# The new code to insert
new_code = """    def provide_code_actions(self, msg_id, params):
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
            actions.append({
                "title": "Rename Symbol",
                "kind": "refactor.rename",
                "command": {
                    "title": "Rename Symbol",
                    "command": "editor.action.rename"
                }
            })

        # Extract Rule / Token
        if start_line == end_line and start_char < end_char:
            selected_text = line_content[start_char:end_char]
            if (selected_text.startswith("'") and selected_text.endswith("'")) or \
               (selected_text.startswith('"') and selected_text.endswith('"')):
                
                # Extract Rule
                new_rule_name = "NewRule"
                content = self.documents.get(uri, "")
                lines = content.split("\\n")
                last_line = len(lines)
                new_rule_text = f"\\n\\nrule {new_rule_name}:\\n    {selected_text}\\nend"
                
                actions.append(self._create_workspace_edit(
                    f"Extract to rule '{new_rule_name}'", uri, [
                        {"range": {"start": {"line": last_line, "character": 0}, "end": {"line": last_line, "character": 0}}, "newText": new_rule_text},
                        {"range": rng, "newText": new_rule_name}
                    ], kind="refactor.extract"
                ))

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
                    token_def = f"        {new_token_name}: {selected_text}\\n"
                    
                    actions.append(self._create_workspace_edit(
                        f"Extract to token '{new_token_name}'", uri, [
                            {"range": {"start": {"line": tokens_end, "character": 0}, "end": {"line": tokens_end, "character": 0}}, "newText": token_def},
                            {"range": rng, "newText": new_token_name}
                        ], kind="refactor.extract"
                    ))
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
                    edits.extend(self.calculate_rename_edits(uri, token_name, upper_name))
            
            elif code == "naming-convention-rule":
                match = re.search(r"Rule '(\w+)'", diag["message"])
                if match:
                    rule_name = match.group(1)
                    pascal_name = rule_name[0].upper() + rule_name[1:]
                    edits.extend(self.calculate_rename_edits(uri, rule_name, pascal_name))
            
            elif code == "missing-grammar-name":
                edits.append({
                    "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}},
                    "newText": "grammar MyGrammar:\\n\\n"
                })

            elif code == "missing-tokens-block":
                content = self.documents.get(uri, "")
                insert_line = 0
                match = re.search(r"grammar\s+\w+:", content)
                if match:
                    insert_line = content.count("\\n", 0, match.end()) + 1
                edits.append({
                    "range": {"start": {"line": insert_line, "character": 0}, "end": {"line": insert_line, "character": 0}},
                    "newText": "    tokens:\\n        # Define tokens here\\n    end\\n\\n"
                })

        if edits:
            # Deduplicate edits based on range and newText
            unique_edits = []
            seen = set()
            for edit in edits:
                key = (
                    edit["range"]["start"]["line"], edit["range"]["start"]["character"],
                    edit["range"]["end"]["line"], edit["range"]["end"]["character"],
                    edit["newText"]
                )
                if key not in seen:
                    seen.add(key)
                    unique_edits.append(edit)

            actions.append(self._create_workspace_edit(
                "Fix all issues", uri, unique_edits, kind="source.fixAll"
            ))
        
        return actions

    # --- Quick Fix Handlers ---

    def _fix_naming_convention_token(self, uri, diag):
        match = re.search(r"Token '(\w+)'", diag["message"])
        if match:
            token_name = match.group(1)
            upper_name = token_name.upper()
            edits = self.calculate_rename_edits(uri, token_name, upper_name)
            return self._create_workspace_edit(
                f"Rename '{token_name}' to '{upper_name}'", uri, edits, diagnostics=[diag]
            )

    def _fix_naming_convention_rule(self, uri, diag):
        match = re.search(r"Rule '(\w+)'", diag["message"])
        if match:
            rule_name = match.group(1)
            pascal_name = rule_name[0].upper() + rule_name[1:]
            edits = self.calculate_rename_edits(uri, rule_name, pascal_name)
            return self._create_workspace_edit(
                f"Rename '{rule_name}' to '{pascal_name}'", uri, edits, diagnostics=[diag]
            )

    def _fix_undefined_reference(self, uri, diag):
        actions = []
        line_idx = diag["range"]["start"]["line"]
        line_content = self._get_line(uri, line_idx)
        
        # Suggestion
        match = re.search(r"Did you mean '(\w+)'\?", diag["message"])
        if match:
            suggestion = match.group(1)
            undefined_match = re.search(r"Undefined reference: '(\w+)'", diag["message"])
            if undefined_match:
                undefined_word = undefined_match.group(1)
                col = line_content.find(undefined_word)
                if col != -1:
                    actions.append(self._create_replace_edit(
                        f"Change to '{suggestion}'", uri, line_idx, col, col + len(undefined_word), suggestion, diag
                    ))

        # Create Rule
        undefined_match = re.search(r"Undefined reference: '(\w+)'", diag["message"])
        if undefined_match:
            new_rule_name = undefined_match.group(1)
            content = self.documents.get(uri, "")
            lines = content.split("\\n")
            last_line = len(lines)
            new_text = f"\\n\\nrule {new_rule_name}:\\n    # TODO: Implement rule\\n    | 'literal'\\nend"
            actions.append(self._create_workspace_edit(
                f"Create rule '{new_rule_name}'", uri, [{
                    "range": {"start": {"line": last_line, "character": 0}, "end": {"line": last_line, "character": 0}},
                    "newText": new_text
                }], diagnostics=[diag]
            ))
        return actions

    def _fix_unreachable_rule(self, uri, diag):
        line_idx = diag["range"]["start"]["line"]
        content = self.documents.get(uri, "")
        lines = content.split("\\n")
        start_line = line_idx
        end_line = start_line
        for i in range(start_line, len(lines)):
            if lines[i].strip() == "end":
                end_line = i
                break
        return self._create_workspace_edit(
            "Delete unreachable rule", uri, [{
                "range": {"start": {"line": start_line, "character": 0}, "end": {"line": end_line + 1, "character": 0}},
                "newText": ""
            }], diagnostics=[diag]
        )

    def _fix_token_shadowing(self, uri, diag):
        match = re.search(r"Token '(\w+)' \(line (\d+)\) has a more general pattern", diag["message"])
        if match:
            shadowing_token = match.group(1)
            shadowing_line = int(match.group(2)) - 1
            line_idx = diag["range"]["start"]["line"]
            line_content = self._get_line(uri, line_idx)
            current_line_text = line_content + "\\n"
            
            return self._create_workspace_edit(
                f"Move before '{shadowing_token}' (Fix shadowing)", uri, [
                    {"range": {"start": {"line": shadowing_line, "character": 0}, "end": {"line": shadowing_line, "character": 0}}, "newText": current_line_text},
                    {"range": {"start": {"line": line_idx, "character": 0}, "end": {"line": line_idx + 1, "character": 0}}, "newText": ""}
                ], diagnostics=[diag]
            )

    def _fix_missing_grammar_name(self, uri, diag):
        return self._create_workspace_edit(
            "Add 'grammar Name:'", uri, [{
                "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}},
                "newText": "grammar MyGrammar:\\n\\n"
            }], diagnostics=[diag]
        )

    def _fix_missing_tokens_block(self, uri, diag):
        content = self.documents.get(uri, "")
        insert_line = 0
        match = re.search(r"grammar\s+\w+:", content)
        if match:
            insert_line = content.count("\\n", 0, match.end()) + 1
        return self._create_workspace_edit(
            "Add 'tokens:' block", uri, [{
                "range": {"start": {"line": insert_line, "character": 0}, "end": {"line": insert_line, "character": 0}},
                "newText": "    tokens:\\n        # Define tokens here\\n    end\\n\\n"
            }], diagnostics=[diag]
        )

    def _fix_rule_missing_tests(self, uri, diag):
        match = re.search(r"Rule '(\w+)'", diag["message"])
        if match:
            rule_name = match.group(1)
            line_idx = diag["range"]["start"]["line"]
            content = self.documents.get(uri, "")
            lines = content.split("\\n")
            insert_line = line_idx + 1
            for i in range(line_idx, len(lines)):
                if lines[i].strip() == "end":
                    insert_line = i + 1
                    break
            new_text = f'\\ntest {rule_name}Tests {rule_name}:\\n    "input" => Result\\nend\\n'
            return self._create_workspace_edit(
                f"Add tests for '{rule_name}'", uri, [{
                    "range": {"start": {"line": insert_line, "character": 0}, "end": {"line": insert_line, "character": 0}},
                    "newText": new_text
                }], diagnostics=[diag]
            )

"""

new_content = content[:start_idx] + new_code + content[end_idx:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Successfully updated server.py")
