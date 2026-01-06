# Router and verification helpers from core/core.py
import json

def format_router_result(result):
    if not result:
        return "No router result."
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        summary = result.get("summary")
        if summary:
            return summary
        return json.dumps(result, indent=2)
    return str(result)

def verify_tool_result(tool_result):
    if not tool_result:
        return False, "No result to verify."
    if isinstance(tool_result, dict):
        if tool_result.get("error"):
            return False, tool_result["error"]
        if tool_result.get("success") is False:
            return False, tool_result.get("message", "Unknown failure.")
        return True, "Success."
    if isinstance(tool_result, str):
        if "error" in tool_result.lower():
            return False, tool_result
        return True, "Success."
    return True, "Success."
