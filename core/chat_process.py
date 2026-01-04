import json
import re
import sys
import time

from core.api import OpenAIClient
from core.config import load_config
from core.history import ConversationHistory
from core.mcp import discover_mcp_tools, run_mcp_tool
from core.skills import list_skills, load_skill, save_skill
from core.system_prompt import seed_history_with_system_prompts
from core.tool_loader import load_tools


def _load_all_tools():
    tools = load_tools()
    mcp_tools = discover_mcp_tools()
    for name, description in mcp_tools.items():
        tools[name] = {
            "run": lambda arguments, n=name: run_mcp_tool(n, arguments),
            "description": f"(MCP) {description}",
        }
    return tools


def _format_tools(tools):
    return "\n".join([f"- {name}: {meta['description']}" for name, meta in tools.items()])


def _collect_response(client, history, on_chunk=None):
    start = time.time()
    response = ""
    for chunk in client.stream_chat(history.get_messages()):
        response += chunk
        if on_chunk:
            on_chunk(chunk)
    elapsed = time.time() - start
    return response, elapsed


def _send(payload):
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def _handle_skill(skill_name, history, client, debug_metrics, debug_lines):
    skill = load_skill(skill_name)
    if not skill:
        return f"Skill '{skill_name}' not found."
    result_lines = [f"Running skill: {skill['name']}"]
    for index, step in enumerate(skill.get("steps", []), start=1):
        result_lines.append(f"[Skill Step {index}] {step}")
        history.add_user_message(f"Skill step: {step}")
        step_response, elapsed = _collect_response(client, history)
        history.add_assistant_message(step_response)
        result_lines.append(step_response.strip())
        if debug_metrics:
            debug_lines.append(f"[DEBUG] Skill step {index} time: {elapsed:.2f}s")
    result_lines.append("[Skill complete. Returning to chat.]")
    return "\n".join(result_lines)


def main():
    config = load_config()
    client = OpenAIClient(config)
    history = ConversationHistory()
    tools = _load_all_tools()
    seed_history_with_system_prompts(history, tools)
    debug_metrics = config.get("debug_metrics", False)

    _send({"type": "ready", "debug": debug_metrics})

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            _send({"type": "error", "content": "Invalid JSON input."})
            continue

        action = request.get("type")
        if action == "shutdown":
            _send({"type": "notification", "content": "Shutting down."})
            break
        if action == "toggle_debug":
            debug_metrics = not debug_metrics
            _send({"type": "notification", "content": f"Debug metrics {'enabled' if debug_metrics else 'disabled'}.", "debug": debug_metrics})
            continue
        if action == "message":
            user_input = request.get("content", "")
            if not user_input:
                _send({"type": "error", "content": "Empty message."})
                continue
        else:
            _send({"type": "error", "content": f"Unknown action '{action}'."})
            continue

        if user_input.lower() in {"exit", "quit"}:
            _send({"type": "notification", "content": "Session closed."})
            break

        debug_lines = []
        aux_messages = []

        # Command handling similar to CLI shortcuts
        if user_input == "!tools":
            aux_messages.append(_format_tools(tools) or "No tools available.")
            _send({"type": "assistant", "content": "\n".join(aux_messages), "debug": debug_lines})
            continue
        if user_input == "!skills":
            skills = list_skills()
            if not skills:
                aux_messages.append("No skills found.")
            else:
                aux_messages.extend([f"- {skill['name']}: {skill.get('description', '')}" for skill in skills])
            _send({"type": "assistant", "content": "\n".join(aux_messages), "debug": debug_lines})
            continue
        if user_input == "!new":
            history = ConversationHistory()
            tools = _load_all_tools()
            seed_history_with_system_prompts(history, tools)
            aux_messages.append("[History cleared]")
            _send({"type": "assistant", "content": "\n".join(aux_messages), "debug": debug_lines})
            continue
        if user_input == "!debug":
            debug_metrics = not debug_metrics
            _send({"type": "notification", "content": f"Debug metrics {'enabled' if debug_metrics else 'disabled'}.", "debug": debug_metrics})
            continue
        if user_input.startswith("!run "):
            response_text = _handle_skill(user_input[5:].strip(), history, client, debug_metrics, debug_lines)
            _send({"type": "assistant", "content": response_text, "debug": debug_lines})
            continue
        if user_input.startswith("!save_skill "):
            try:
                payload = user_input[len("!save_skill "):]
                name, desc, steps = payload.split("|", 2)
                steps_list = [step.strip() for step in steps.split(";") if step.strip()]
                save_skill(name.strip(), desc.strip(), steps_list)
                aux_messages.append(f"Skill '{name.strip()}' saved.")
            except Exception as exc:
                aux_messages.append(f"Failed to save skill: {exc}")
            _send({"type": "assistant", "content": "\n".join(aux_messages), "debug": debug_lines})
            continue
        if user_input.startswith("!"):
            parts = user_input[1:].split(maxsplit=1)
            toolname = parts[0]
            toolarg = parts[1] if len(parts) > 1 else ""
            if toolname in tools:
                try:
                    result = tools[toolname]["run"](toolarg)
                except Exception as exc:
                    result = f"Tool '{toolname}' failed: {exc}"
            else:
                result = f"Tool '{toolname}' not found."
            _send({"type": "assistant", "content": str(result), "debug": debug_lines})
            continue

        history.add_user_message(user_input)

        router_prompt = (
            "Does the following user request require a multi-step plan (tools/actions) or can it be answered directly? "
            "Reply with 'plan' or 'respond'. Request: '" + user_input + "'"
        )
        history.add_user_message(router_prompt)
        router_response, _ = _collect_response(client, history)
        decision = router_response.strip().lower()
        if history.memory[0] and history.memory[0][-1]["role"] == "user" and router_prompt in history.memory[0][-1]["content"]:
            history.memory[0].pop()

        if "plan" in decision:
            plan_prompt = (
                "Given the user's request, break it down into a numbered list of concrete steps (tools or actions) to achieve the goal. "
                f"Only plan up to {config.get('chain_limit', 25)} steps. Respond with the plan as a numbered list."
            )
            history.add_user_message(plan_prompt)
            plan_response, plan_elapsed = _collect_response(client, history)
            if debug_metrics:
                debug_lines.append(f"[DEBUG] Planning time: {plan_elapsed:.2f}s")
            steps = re.findall(r"\d+\.\s*(.*)", plan_response)
            if not steps:
                aux_messages.append("[No plan steps found. Try rephrasing your request.]")
                _send({"type": "assistant", "content": "\n".join(aux_messages), "debug": debug_lines})
                continue
            chain_history = []
            t_chain_start = time.time()
            for step in steps[: config.get("chain_limit", 25)]:
                history.add_user_message(f"Step: {step}")
                step_response, step_elapsed = _collect_response(client, history)
                history.add_assistant_message(step_response)
                chain_history.append({"step": step, "response": step_response.strip()})
                if debug_metrics:
                    debug_lines.append(f"[DEBUG] Step time: {step_elapsed:.2f}s")
            t_chain_end = time.time()
            summary_prompt = (
                f"Provide a response that is appropriate based on the user's prompt: '{user_input}'.\n"
                "Knowing these Steps and results:\n" +
                "\n".join([f"Step: {entry['step']}\nResult: {entry['response']}" for entry in chain_history])
            )
            history.add_user_message(summary_prompt)
            summary_response, summary_elapsed = _collect_response(client, history)
            if debug_metrics:
                debug_lines.append(f"[DEBUG] Chain steps: {len(chain_history)} | Chain time: {t_chain_end - t_chain_start:.2f}s")
                debug_lines.append(f"[DEBUG] Summary time: {summary_elapsed:.2f}s")
            _send({
                "type": "assistant",
                "content": summary_response.strip(),
                "debug": debug_lines,
                "extras": aux_messages + ["[Chain complete. Returning to chat.]"]
            })
        else:
            direct_response, direct_elapsed = _collect_response(client, history)
            if debug_metrics:
                debug_lines.append(f"[DEBUG] Response time: {direct_elapsed:.2f}s")
            _send({"type": "assistant", "content": direct_response.strip(), "debug": debug_lines, "extras": aux_messages})


if __name__ == "__main__":
    main()
