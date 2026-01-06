import pytest
from core.functions.run_mcp_tool import run_mcp_tool

def test_run_mcp_tool_success(monkeypatch):
    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"result": "ok"}
    monkeypatch.setattr("requests.post", lambda *a, **k: Resp())
    assert run_mcp_tool("foo", {}) == "ok"

def test_run_mcp_tool_error(monkeypatch):
    def fail_post(*a, **k):
        raise Exception("fail")
    monkeypatch.setattr("requests.post", fail_post)
    result = run_mcp_tool("foo", {})
    assert result.startswith("MCP tool error:")
