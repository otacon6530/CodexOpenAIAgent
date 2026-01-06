from core.classes.MCP import MCP

def test_mcp_discover_tools():
    mcp = MCP(discover_func=lambda: {"tool1": "desc1", "tool2": "desc2"})
    result = mcp.discover_tools()
    assert result == {"tool1": "desc1", "tool2": "desc2"}

def test_mcp_run_tool():
    mcp = MCP(run_func=lambda name, args: f"ran {name} with {args}")
    result = mcp.run_tool("foo", {"bar": 1})
    assert result == "ran foo with {'bar': 1}"
