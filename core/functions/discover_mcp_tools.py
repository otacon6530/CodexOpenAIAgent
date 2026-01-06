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
