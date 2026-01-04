import requests

MCP_SERVER_URL = "http://localhost:8000/tools"

discovered_tools = {}

def discover_mcp_tools():
    try:
        resp = requests.get(MCP_SERVER_URL, timeout=5)
        resp.raise_for_status()
        tools = resp.json()
        for tool in tools:
            discovered_tools[tool["name"]] = tool["description"]
        return discovered_tools
    except Exception:
        return {}

def run_mcp_tool(toolname, args):
    try:
        resp = requests.post(f"{MCP_SERVER_URL}/{toolname}", json={"args": args}, timeout=30)
        resp.raise_for_status()
        return resp.json().get("result", "(No result)")
    except Exception as exc:
        return f"MCP tool error: {exc}"
