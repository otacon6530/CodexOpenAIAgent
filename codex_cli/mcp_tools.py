import requests

# Example: MCP server URL from config or hardcoded for now
MCP_SERVER_URL = 'http://localhost:8000/tools'

# Cache for discovered MCP tools
discovered_tools = {}

def discover_mcp_tools():
    """Query the MCP server for available tools and return as a dict."""
    try:
        resp = requests.get(MCP_SERVER_URL, timeout=5)
        resp.raise_for_status()
        tools = resp.json()  # Expecting a list of {name, description}
        for tool in tools:
            discovered_tools[tool['name']] = tool['description']
        return discovered_tools
    except Exception as e:
        return {}

def run_mcp_tool(toolname, args):
    """Call a tool on the MCP server and return its result."""
    try:
        resp = requests.post(f'{MCP_SERVER_URL}/{toolname}', json={'args': args}, timeout=30)
        resp.raise_for_status()
        return resp.json().get('result', '(No result)')
    except Exception as e:
        return f'MCP tool error: {e}'
