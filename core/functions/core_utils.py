# Utility functions refactored from core/core.py
import json
import re
import sys
import time

def load_all_tools(load_tools, discover_mcp_tools, run_mcp_tool):
    tools = load_tools()
    mcp_tools = discover_mcp_tools()
    for name, description in mcp_tools.items():
        tools[name] = {
            "run": lambda arguments, n=name: run_mcp_tool(n, arguments),
            "description": f"(MCP) {description}",
        }
    return tools

def format_tools(tools):
    return "\n".join([f"- {name}: {meta['description']}" for name, meta in tools.items()])

def parse_editor_payload(arguments):
    text = (arguments or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        return {"value": data}
    except json.JSONDecodeError:
        return {"path": text}
