import pytest
from core.functions import editor_tools

def test_inject_editor_tools_basic():
    tools = {}
    def dummy_query(name, payload=None):
        return {"summary": {"error": 1, "warning": 2, "information": 3, "hint": 4}, "total": 10, "returned": 5, "truncated": False, "items": []}
    def dummy_parse(payload):
        return {"foo": "bar"}
    editor_tools.inject_editor_tools(tools, dummy_query, dummy_parse)
    assert "editor.diagnostics" in tools
    assert callable(tools["editor.diagnostics"]["run"])
