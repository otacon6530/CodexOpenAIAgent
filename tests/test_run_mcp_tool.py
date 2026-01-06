from core.functions.run_mcp_tool import run_mcp_tool

def test_run_mcp_tool(monkeypatch):
    def fake_post(*a, **k):
        class Resp:
            def raise_for_status(self): pass
            def json(self): return {"result": "ok"}
        return Resp()
    import core.functions.run_mcp_tool as mod
    monkeypatch.setattr(mod.requests, "post", fake_post)
    result = run_mcp_tool("foo", {})
    assert result == "ok"
