import argparse
import re
import shutil
import time

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.styles import Style

from core.api import OpenAIClient
from core.config import load_config
from core.history import ConversationHistory
from core.mcp import discover_mcp_tools, run_mcp_tool
from core.tool_loader import load_tools
from core.skills import list_skills, load_skill, save_skill
from core.system_prompt import seed_history_with_system_prompts


def _append_log(chat_log, style_name, message):
    chat_log.append((style_name, message))

def _render_chat(chat_log, style):
    try:
        height = shutil.get_terminal_size().lines
    except Exception:
        height = 24
    chat_lines = sum(entry[1].count("\n") + 1 for entry in chat_log)
    pad_lines = max(0, height - chat_lines - 2)
    if pad_lines > 0:
        print("\n" * pad_lines, end="")
    print_formatted_text(FormattedText(chat_log), style=style)


def _list_tools_lines(tools):
    return [("", "Available tools:")] + [("class:tool", f"- {name}: {tool['description']}") for name, tool in tools.items()]


def _list_skills_lines():
    skills = list_skills()
    if not skills:
        return [("class:tool", "No skills found.")]
    lines = [("", "Skills:")]
    for skill in skills:
        desc = skill.get("description", "")
        lines.append(("class:tool", f"- {skill['name']}: {desc}"))
    return lines


def _run_skill(name, history, client, chat_log, debug_metrics):
    skill = load_skill(name)
    if not skill:
        _append_log(chat_log, "class:tool", f"Skill '{name}' not found.")
        return
    _append_log(chat_log, "class:tool", f"Running skill: {skill['name']}")
    for index, step in enumerate(skill.get("steps", []), start=1):
        _append_log(chat_log, "class:tool", f"[Skill Step {index}] {step}")
        history.add_user_message(f"Skill step: {step}")
        step_response, elapsed = _collect_response(client, history)
        history.add_assistant_message(step_response)
        _append_log(chat_log, "class:assistant", step_response.strip())
        if debug_metrics:
            _append_log(chat_log, "class:tool", f"[DEBUG] Skill step time: {elapsed:.2f}s")
    _append_log(chat_log, "class:tool", "[Skill complete. Returning to user input.]")


def _save_skill(payload, chat_log):
    try:
        name, desc, steps = payload.split("|", 2)
        steps_list = [step.strip() for step in steps.split(";") if step.strip()]
        save_skill(name.strip(), desc.strip(), steps_list)
        _append_log(chat_log, "class:tool", f"Skill '{name.strip()}' saved.")
    except Exception as exc:
        _append_log(chat_log, "class:tool", f"Failed to save skill: {exc}")


def _collect_response(client, history, on_chunk=None):
    start = time.time()
    response = ""
    for chunk in client.stream_chat(history.get_messages()):
        response += chunk
        if on_chunk:
            on_chunk(chunk)
    elapsed = time.time() - start
    return response, elapsed


def main(argv=None):
    parser = argparse.ArgumentParser(description="codex-agent CLI")
    parser.add_argument("--exec", dest="exec_message", type=str, help="Send a single message and exit")
    args = parser.parse_args(argv)

    config = load_config()
    client = OpenAIClient(config)
    history = ConversationHistory()
    tools = load_tools()
    mcp_tools = discover_mcp_tools()
    for name, description in mcp_tools.items():
        tools[name] = {
            "run": lambda arguments, n=name: run_mcp_tool(n, arguments),
            "description": f"(MCP) {description}",
        }
    seed_history_with_system_prompts(history, tools)

    if args.exec_message:
        message = args.exec_message
        if message.startswith("!"):
            parts = message[1:].split(maxsplit=1)
            toolname = parts[0]
            toolarg = parts[1] if len(parts) > 1 else ""
            if toolname in tools:
                print(tools[toolname]["run"](toolarg))
            else:
                print(f"Tool '{toolname}' not found.")
            return
        history.add_user_message(message)
        response, elapsed = _collect_response(
            client,
            history,
            on_chunk=lambda chunk: print(chunk, end="", flush=True),
        )
        print()
        if config.get("debug_metrics", False):
            print(f"[DEBUG] Response time: {elapsed:.2f}s")
        return

    session = PromptSession()
    style = Style.from_dict({
        "user": "ansicyan",
        "assistant": "ansiyellow",
        "tool": "ansigreen",
    })
    chat_log = []
    debug_metrics = config.get("debug_metrics", False)
    chain_limit = config.get("chain_limit", 25)

    print("codex-agent CLI (type 'exit' to quit)")
    with patch_stdout():
        while True:
            try:
                session.app.renderer.clear()
                _render_chat(chat_log, style)
                user_input = session.prompt([( "class:user", "You: " )], refresh_interval=0.1)
                if user_input.lower() in {"exit", "quit"}:
                    break
                if not user_input:
                    continue

                if user_input == "!tools":
                    chat_log.extend(_list_tools_lines(tools))
                    continue
                if user_input == "!skills":
                    chat_log.extend(_list_skills_lines())
                    continue
                if user_input == "!new":
                    history = ConversationHistory()
                    tools = load_tools()
                    mcp_tools = discover_mcp_tools()
                    for name, description in mcp_tools.items():
                        tools[name] = {
                            "run": lambda arguments, n=name: run_mcp_tool(n, arguments),
                            "description": f"(MCP) {description}",
                        }
                    seed_history_with_system_prompts(history, tools)
                    chat_log.clear()
                    chat_log.append(("", "[History cleared]"))
                    continue
                if user_input == "!debug":
                    debug_metrics = not debug_metrics
                    state = "enabled" if debug_metrics else "disabled"
                    _append_log(chat_log, "class:tool", f"[Debug metrics {state}]")
                    continue
                if user_input.startswith("!run "):
                    _run_skill(user_input[5:].strip(), history, client, chat_log, debug_metrics)
                    continue
                if user_input.startswith("!save_skill "):
                    _save_skill(user_input[len("!save_skill "):], chat_log)
                    continue
                if user_input.startswith("!"):
                    parts = user_input[1:].split(maxsplit=1)
                    toolname = parts[0]
                    toolarg = parts[1] if len(parts) > 1 else ""
                    if toolname in tools:
                        result = tools[toolname]["run"](toolarg)
                        _append_log(chat_log, "class:tool", result)
                    else:
                        _append_log(chat_log, "class:tool", f"Tool '{toolname}' not found.")
                    continue

                history.add_user_message(user_input)
                _append_log(chat_log, "class:user", f"You: {user_input}\n")

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
                        f"Only plan up to {chain_limit} steps. Respond with the plan as a numbered list."
                    )
                    history.add_user_message(plan_prompt)
                    plan_response, plan_elapsed = _collect_response(client, history)
                    if debug_metrics:
                        _append_log(chat_log, "class:tool", f"[DEBUG] Planning time: {plan_elapsed:.2f}s")
                    steps = re.findall(r"\d+\.\s*(.*)", plan_response)
                    if not steps:
                        _append_log(chat_log, "class:tool", "[No plan steps found. Proceeding with normal chat.]")
                        continue
                    chain_history = []
                    t_chain_start = time.time()
                    for step in steps[:chain_limit]:
                        history.add_user_message(f"Step: {step}")
                        step_response, step_elapsed = _collect_response(client, history)
                        history.add_assistant_message(step_response)
                        chain_history.append({"step": step, "response": step_response.strip()})
                        if debug_metrics:
                            _append_log(chat_log, "class:tool", f"[DEBUG] Step time: {step_elapsed:.2f}s")
                    t_chain_end = time.time()
                    summary_prompt = (
                        f"Provide a response that is appropriate based on the user's prompt: '{user_input}'.\n"
                        "Knowing these Steps and results:\n" +
                        "\n".join([f"Step: {entry['step']}\nResult: {entry['response']}" for entry in chain_history])
                    )
                    history.add_user_message(summary_prompt)
                    summary_response, summary_elapsed = _collect_response(client, history)
                    _append_log(chat_log, "class:assistant", summary_response.strip())
                    if debug_metrics:
                        _append_log(chat_log, "class:tool", f"[DEBUG] Chain steps: {len(chain_history)} | Chain time: {t_chain_end - t_chain_start:.2f}s")
                        _append_log(chat_log, "class:tool", f"[DEBUG] Summary time: {summary_elapsed:.2f}s")
                    _append_log(chat_log, "class:tool", "\n[Chain complete. Returning to user input.]")
                else:
                    direct_response, direct_elapsed = _collect_response(client, history)
                    _append_log(chat_log, "class:assistant", direct_response.strip())
                    if debug_metrics:
                        _append_log(chat_log, "class:tool", f"[DEBUG] Response time: {direct_elapsed:.2f}s")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break

if __name__ == "__main__":
    main()
