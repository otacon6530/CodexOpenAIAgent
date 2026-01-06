from core.functions.discover_mcp_tools import discover_mcp_tools

def test_discover_mcp_tools(monkeypatch):
    def fake_get(*a, **k):
        class Resp:
            def raise_for_status(self): pass
            def json(self): return [{"name": "foo", "description": "bar"}]
        return Resp()
    import core.functions.discover_mcp_tools as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)
    tools = discover_mcp_tools()
    assert "foo" in tools
