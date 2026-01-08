from core.functions.load_skill import load_skill
from core.functions.llm_response import collect_response


def _handle_skill(skill_name, history, client, tools, debug_metrics, debug_lines):
    skill = load_skill(skill_name)
    if not skill:
        return f"Skill '{skill_name}' not found."
    result_lines = [f"Running skill: {skill['name']}"]
    for index, step in enumerate(skill.get("steps", []), start=1):
        result_lines.append(f"[Skill Step {index}] {step}")
        history.add_user_message(f"Skill step: {step}")
        step_response, elapsed = collect_response(client, history, tools)
        history.add_assistant_message(step_response)
        result_lines.append(step_response.strip())
        if debug_metrics:
            debug_lines.append(f"[DEBUG] Skill step {index} time: {elapsed:.2f}s")
    result_lines.append("[Skill complete. Returning to chat.]")
    return "\n".join(result_lines)