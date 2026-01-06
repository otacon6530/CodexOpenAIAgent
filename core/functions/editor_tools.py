# Editor tool injection and helpers from core/core.py
import json

def inject_editor_tools(tools, request_editor_query, parse_editor_payload):
    def as_json(result):
        return json.dumps(result, indent=2)

    def format_diagnostics(result):
        if not isinstance(result, dict):
            return as_json(result)
        summary = result.get("summary", {})
        total = result.get("total")
        returned = result.get("returned")
        truncated = result.get("truncated")
        lines = []
        lines.append("Diagnostics Summary:")
        lines.append(
            f"  Errors: {summary.get('error', 0)} | Warnings: {summary.get('warning', 0)} | "
            f"Info: {summary.get('information', 0)} | Hints: {summary.get('hint', 0)}"
        )
        lines.append(f"  Returned: {returned} of {total}{' (truncated)' if truncated else ''}")
        items = result.get("items") or []
        if not items:
            lines.append("No diagnostics reported.")
            return "\n".join(lines)
        severity_order = ["error", "warning", "information", "hint"]
        per_file_limit = 5
        lines.append("\nFiles:")
        for entry in items:
            file_path = entry.get("uri") or entry.get("file") or "(unknown file)"
            diagnostics = entry.get("diagnostics") or []
            if not diagnostics:
                continue
            lines.append(f"  {file_path}")
            def sort_key(diag):
                severity = diag.get("severity", "hint")
                try:
                    severity_index = severity_order.index(severity)
                except ValueError:
                    severity_index = len(severity_order)
                rng = diag.get("range", {})
                start = rng.get("start", {})
                return (severity_index, start.get("line", 0), start.get("character", 0))
            sorted_diags = sorted(diagnostics, key=sort_key)
            for diag in sorted_diags[:per_file_limit]:
                severity = diag.get("severity", "unknown").capitalize()
                rng = diag.get("range", {})
                start = rng.get("start", {})
                message = diag.get("message", "(no message)")
                code = diag.get("code")
                source = diag.get("source")
                location = f"L{start.get('line', '?')}:{start.get('character', '?')}"
                extra = []
                if source:
                    extra.append(str(source))
                if code:
                    extra.append(str(code))
                extra_text = f" ({', '.join(extra)})" if extra else ""
                lines.append(f"    - {severity} {location}{extra_text}: {message}")
            if len(sorted_diags) > per_file_limit:
                lines.append(f"    … {len(sorted_diags) - per_file_limit} more entries")
        return "\n".join(lines)
    def diagnostics_tool(arguments):
        payload = parse_editor_payload(arguments)
        try:
            result = request_editor_query("diagnostics", payload or None)
        except Exception as exc:
            return f"Diagnostics query failed: {exc}"
        return format_diagnostics(result)
    def open_editors_tool(arguments):
        try:
            result = request_editor_query("open_editors")
        except Exception as exc:
            return f"Open editors query failed: {exc}"
        return as_json(result)
    def workspace_info_tool(arguments):
        try:
            result = request_editor_query("workspace_info")
        except Exception as exc:
            return f"Workspace info query failed: {exc}"
        return as_json(result)
    def document_symbols_tool(arguments):
        payload = parse_editor_payload(arguments)
        if not payload:
            payload = {}
        try:
            result = request_editor_query("document_symbols", payload)
        except Exception as exc:
            return f"Document symbols query failed: {exc}"
        return as_json(result)
    tools["editor.diagnostics"] = {
        "run": diagnostics_tool,
        "description": "Inspect VS Code diagnostics. Args: optional JSON with path/severity/limit or a file path string.",
    }
    tools["editor.open_editors"] = {
        "run": open_editors_tool,
        "description": "List currently visible editors and selections in VS Code.",
    }
    tools["editor.workspace_info"] = {
        "run": workspace_info_tool,
        "description": "Fetch workspace folders and active file from VS Code.",
    }
    tools["editor.document_symbols"] = {
        "run": document_symbols_tool,
        "description": "List document symbols for the active file or a provided path (JSON input: {\"path\": ...}).",
    }
