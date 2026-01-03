import subprocess
import json


def exec_command(cmd: str, max_output_tokens: int = 512, **kwargs) -> dict:
    """
    Executes a shell command and returns the output (truncated to max_output_tokens chars).
    """
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        # Truncate output to max_output_tokens (approx chars)
        if len(output) > max_output_tokens:
            output = output[:max_output_tokens] + "... [truncated]"
        return {
            "output": output,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "output": f"[ERROR] {str(e)}",
            "returncode": -1
        }

# Add stubs for other tools as needed
def list_mcp_resources(**kwargs):
    return {"output": "[list_mcp_resources not implemented]"}

def list_mcp_resource_templates(**kwargs):
    return {"output": "[list_mcp_resource_templates not implemented]"}

def read_mcp_resource(**kwargs):
    return {"output": "[read_mcp_resource not implemented]"}

def update_plan(**kwargs):
    return {"output": "[update_plan not implemented]"}

def apply_patch(**kwargs):
    return {"output": "[apply_patch not implemented]"}

def view_image(**kwargs):
    return {"output": "[view_image not implemented]"}

# Tool registry for dynamic dispatch
tool_registry = {
    "exec_command": exec_command,
    "list_mcp_resources": list_mcp_resources,
    "list_mcp_resource_templates": list_mcp_resource_templates,
    "read_mcp_resource": read_mcp_resource,
    "update_plan": update_plan,
    "apply_patch": apply_patch,
    "view_image": view_image,
}

def run_tool(tool_name: str, arguments: dict) -> dict:
    func = tool_registry.get(tool_name)
    if not func:
        return {"output": f"[ERROR] Tool '{tool_name}' not found."}
    return func(**arguments)
