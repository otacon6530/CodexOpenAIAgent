import pytest
from core.functions import router_utils

def test_format_router_result():
    result = {"summary": "Router summary"}
    assert router_utils.format_router_result(result) == "Router summary"
    assert "No router result" in router_utils.format_router_result("")

def test_verify_tool_result():
    assert router_utils.verify_tool_result({"error": "fail"}) == (False, "fail")
    assert router_utils.verify_tool_result({"success": False, "message": "fail"}) == (False, "fail")
    assert router_utils.verify_tool_result({"success": True}) == (True, "Success.")
    assert router_utils.verify_tool_result("error: fail") == (False, "error: fail")
    assert router_utils.verify_tool_result("ok") == (True, "Success.")
