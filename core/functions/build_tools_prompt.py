def build_tools_prompt(tools):
    lines = ["Available tools:"]
    for name, tool in tools.items():
        description = tool.get("description", "")
        if name == "create_file":
            description += " Example: <tool:create_file>test.txt|hello world</tool> creates test.txt with 'hello world'. Prefer this over shell commands for file creation."
        lines.append(f"- {name}: {description}")
    lines.append("IMPORTANT: To call a tool, you MUST reply with <tool:toolname>arguments</tool>. Do NOT use <shell>...</shell> or any other format, or your tool call will be ignored.")
    lines.append("Example: <tool:shell>echo hello > test.txt</tool>")
    return "\n".join(lines)
