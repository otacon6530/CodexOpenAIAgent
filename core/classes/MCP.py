
from core.functions.discover_mcp_tools import discover_mcp_tools
from core.functions.run_mcp_tool import run_mcp_tool

class MCP:
    def __init__(self, server_url="http://localhost:8000/tools", discover_func=None, run_func=None):
        self.server_url = server_url
        self._discover_func = discover_func or discover_mcp_tools
        self._run_func = run_func or run_mcp_tool

    def discover_tools(self):
        return self._discover_func()

    def run_tool(self, toolname, args):
        return self._run_func(toolname, args)
