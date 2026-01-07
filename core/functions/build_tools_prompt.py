def build_tools_prompt(tools):
    lines = ["Available tools:"]
    for name, tool in tools.items():
        description = tool.get("description", "")
        lines.append(f"- {name}: {description}")
        # Provide an explicit example for each tool
        if name == "shell":
            lines.append("  Example: <tool:shell>echo hello > test.txt</tool>")
        elif name == "editor.diagnostics":
            lines.append("  Example: <tool:editor.diagnostics>{\"path\": \"src/app.py\"}</tool>")
        elif name == "editor.open_editors":
            lines.append("  Example: <tool:editor.open_editors></tool>")
        elif name == "editor.workspace_info":
            lines.append("  Example: <tool:editor.workspace_info></tool>")
        elif name == "editor.document_symbols":
            lines.append("  Example: <tool:editor.document_symbols>{\"path\": \"src/app.py\"}</tool>")
        elif name == "create_file":
            lines.append("  Example: <tool:create_file>test.txt|hello world</tool>")
    lines.append("IMPORTANT: To call a tool, you MUST reply with <tool:toolname>arguments</tool>. Do NOT use <shell>...</shell> or any other format, or your tool call will be ignored.")
    return "\n".join(lines)
