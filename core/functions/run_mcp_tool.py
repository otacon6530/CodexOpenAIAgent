import requests

MCP_SERVER_URL = "http://localhost:8000/tools"

def run_mcp_tool(toolname, args):
    try:
        resp = requests.post(f"{MCP_SERVER_URL}/{toolname}", json={"args": args}, timeout=30)
        resp.raise_for_status()
        return resp.json().get("result", "(No result)")
    except Exception as exc:
        return f"MCP tool error: {exc}"
