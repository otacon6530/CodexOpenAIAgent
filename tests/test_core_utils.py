import pytest
from core.functions import core_utils

def test_format_tools():
    tools = {
        "tool1": {"description": "desc1"},
        "tool2": {"description": "desc2"}
    }
    formatted = core_utils.format_tools(tools)
    assert "tool1" in formatted and "tool2" in formatted

def test_parse_editor_payload():
    assert core_utils.parse_editor_payload('{"foo": "bar"}') == {"foo": "bar"}
    assert core_utils.parse_editor_payload('') == {}
    assert core_utils.parse_editor_payload(None) == {}

def test_load_all_tools():
    # Dummy functions for testing
    def dummy_load_tools():
        return {"tool1": {"description": "desc1"}}
    def dummy_discover_mcp_tools():
        return {"tool2": "desc2"}
    def dummy_run_mcp_tool(name, args):
        return f"ran {name} with {args}"
    tools = core_utils.load_all_tools(dummy_load_tools, dummy_discover_mcp_tools, dummy_run_mcp_tool)
    assert isinstance(tools, dict)
    assert "tool1" in tools and "tool2" in tools
