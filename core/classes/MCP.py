from core.mcp_object import MCP as MCPObject

class MCP:
    def __init__(self, server_url="http://localhost:8000/tools"):
        self.mcp = MCPObject(server_url)

    def discover_tools(self):
        return self.mcp.discover_tools()

    def run_tool(self, toolname, args):
        return self.mcp.run_tool(toolname, args)
