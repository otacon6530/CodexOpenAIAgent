# Agentic planning and summary helpers from core/core.py
import json

def summarize_plan(plan):
    if not plan:
        return "No plan generated."
    if isinstance(plan, str):
        return plan
    if isinstance(plan, dict):
        steps = plan.get("steps")
        if steps:
            return "\n".join(f"- {step}" for step in steps)
        summary = plan.get("summary")
        if summary:
            return summary
        return json.dumps(plan, indent=2)
    if isinstance(plan, list):
        return "\n".join(str(step) for step in plan)
    return str(plan)

def summarize_tool_use(tool_calls):
    if not tool_calls:
        return "No tool calls."
    lines = []
    for call in tool_calls:
        name = call.get("name", "(unknown tool)")
        args = call.get("args", {})
        result = call.get("result", "(no result)")
        lines.append(f"Tool: {name}\n  Args: {json.dumps(args)}\n  Result: {str(result)[:200]}")
    return "\n".join(lines)
