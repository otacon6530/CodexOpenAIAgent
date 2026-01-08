
from core.functions.load_tools import load_tools
from core.functions.discover_mcp_tools import discover_mcp_tools
from core.functions.run_mcp_tool import run_mcp_tool

def _load_all_tools():
    tools = load_tools()
    mcp_tools = discover_mcp_tools()
    for name, description in mcp_tools.items():
        tools[name] = {
            "run": lambda arguments, n=name: run_mcp_tool(n, arguments),
            "description": f"(MCP) {description}",
        }
    return tools