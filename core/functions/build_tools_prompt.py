def build_tools_prompt(tools):
    lines = ["Available tools:"]
    for name, tool in tools.items():
        description = tool.get("description", "")
        if name == "create_file":
            description += " Example: <tool:create_file>test.txt|hello world</tool> creates test.txt with 'hello world'. Prefer this over shell commands for file creation."
        lines.append(f"- {name}: {description}")
    lines.append("To call a tool, reply with <tool:name>args</tool>.")
    return "\n".join(lines)
