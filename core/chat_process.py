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

TOOL_PATTERN = re.compile(r"<tool:([a-zA-Z0-9_.\-]+)>(.*?)</tool>", re.DOTALL)
_PENDING_MESSAGES = []


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



def _process_tool_calls(response_text, history, client, tools, config, debug_lines, debug_metrics):
    max_iterations = max(1, int(config.get("tool_iterations", 3)))
    tool_messages = []
    text = response_text.strip()
    iterations = 0
    shell_approve_all = getattr(_process_tool_calls, "shell_approve_all", False)
    shell_approval_cache = getattr(_process_tool_calls, "shell_approval_cache", {})

    def request_shell_approval(command):
        import uuid
        approval_id = str(uuid.uuid4())
        _send({
            "type": "shell_approval_request",
            "command": command,
            "id": approval_id
        })
        response = _wait_for_message("shell_approval_response", approval_id)
        if response is None:
            return False, False
        return response.get("approved", False), response.get("approve_all", False)

    while True:
        history.add_assistant_message(text)
        matches = list(TOOL_PATTERN.finditer(text))
        if not matches:
            break
        if iterations >= max_iterations:
            tool_messages.append("[Tool execution limit reached]")
            break

        iterations += 1
        for match in matches:
            tool_name = match.group(1).strip()
            tool_args = match.group(2).strip()
            if tool_name == "shell":
                # Approval required for shell commands
                if not shell_approve_all:
                    cache_key = tool_args.strip()
                    if cache_key in shell_approval_cache:
                        approved, approve_all = shell_approval_cache[cache_key]
                    else:
                        approved, approve_all = request_shell_approval(tool_args)
                        shell_approval_cache[cache_key] = (approved, approve_all)
                    if approve_all:
                        shell_approve_all = True
                        _process_tool_calls.shell_approve_all = True
                    if not approved:
                        message = f"[Tool shell] Command denied by user."
                        history.add_system_message(message)
                        tool_messages.append(message)
                        continue
            if tool_name in tools:
                try:
                    output = tools[tool_name]["run"](tool_args)
                    message = f"[Tool {tool_name}] {output if output else '(No output)'}"
                except Exception as exc:
                    message = f"[Tool {tool_name}] Error: {exc}"
            else:
                message = f"[Tool {tool_name}] not found."
            history.add_system_message(message)
            tool_messages.append(message)
            if debug_metrics:
                preview = tool_args[:40] + ("…" if len(tool_args) > 40 else "")
                debug_lines.append(f"[DEBUG] Tool {tool_name} invoked with args: {preview}")

        # Prompt the LLM to summarize/explain the tool output for the user
        history.add_user_message("Please summarize or explain the result of the previous tool call for the user.")
        followup_response, followup_elapsed = _collect_response(client, history)
        text = followup_response.strip()
        if debug_metrics:
            debug_lines.append(f"[DEBUG] Tool follow-up time: {followup_elapsed:.2f}s")

    cleaned = TOOL_PATTERN.sub('', text)
    return cleaned, tool_messages


def _send(payload):
    try:
        debug_message = json.dumps(payload)
    except Exception:
        debug_message = str(payload)
    print(f"[DEBUG] Sending to extension: {debug_message}", file=sys.stderr)
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def _read_raw_message():
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            _send({"type": "error", "content": "Invalid JSON input."})


def _pop_buffered_message(expected_type=None, expected_id=None):
    if not _PENDING_MESSAGES:
        return None
    if expected_type is None:
        return _PENDING_MESSAGES.pop(0)
    for index, message in enumerate(_PENDING_MESSAGES):
        if message.get("type") != expected_type:
            continue
        if expected_id is not None and message.get("id") != expected_id:
            continue
        return _PENDING_MESSAGES.pop(index)
    return None


def _next_message():
    buffered = _pop_buffered_message()
    if buffered is not None:
        return buffered
    return _read_raw_message()


def _wait_for_message(expected_type, expected_id=None, timeout=None):
    if expected_type is None:
        raise ValueError("expected_type is required")

    deadline = time.time() + timeout if timeout else None

    buffered = _pop_buffered_message(expected_type, expected_id)
    if buffered is not None:
        return buffered

    while True:
        if deadline is not None and time.time() > deadline:
            return None
        message = _read_raw_message()
        if message is None:
            return None
        if message.get("type") == expected_type and (expected_id is None or message.get("id") == expected_id):
            return message
        _PENDING_MESSAGES.append(message)


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


def _request_editor_query(query, payload=None, timeout=10):
    import uuid

    request_id = str(uuid.uuid4())
    message = {"type": "editor_query", "query": query, "id": request_id}
    if payload is not None:
        message["payload"] = payload

    _send(message)

    response = _wait_for_message("editor_query_response", request_id, timeout=timeout)
    if response is None:
        raise RuntimeError("No response from VS Code extension.")
    if response.get("error"):
        raise RuntimeError(response.get("error"))
    return response.get("result")


def _parse_editor_payload(arguments):
    text = (arguments or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        return {"value": data}
    except json.JSONDecodeError:
        return {"path": text}


def _inject_editor_tools(tools):
    def as_json(result):
        return json.dumps(result, indent=2)

    def format_diagnostics(result):
        if not isinstance(result, dict):
            return as_json(result)

        summary = result.get("summary", {})
        total = result.get("total")
        returned = result.get("returned")
        truncated = result.get("truncated")

        lines = []
        lines.append("Diagnostics Summary:")
        lines.append(
            f"  Errors: {summary.get('error', 0)} | Warnings: {summary.get('warning', 0)} | "
            f"Info: {summary.get('information', 0)} | Hints: {summary.get('hint', 0)}"
        )
        lines.append(f"  Returned: {returned} of {total}{' (truncated)' if truncated else ''}")

        items = result.get("items") or []
        if not items:
            lines.append("No diagnostics reported.")
            return "\n".join(lines)

        severity_order = ["error", "warning", "information", "hint"]
        per_file_limit = 5
        lines.append("\nFiles:")
        for entry in items:
            file_path = entry.get("uri") or entry.get("file") or "(unknown file)"
            diagnostics = entry.get("diagnostics") or []
            if not diagnostics:
                continue

            lines.append(f"  {file_path}")
            # Sort diagnostics by severity order then range start line
            def sort_key(diag):
                severity = diag.get("severity", "hint")
                try:
                    severity_index = severity_order.index(severity)
                except ValueError:
                    severity_index = len(severity_order)
                rng = diag.get("range", {})
                start = rng.get("start", {})
                return (severity_index, start.get("line", 0), start.get("character", 0))

            sorted_diags = sorted(diagnostics, key=sort_key)
            for diag in sorted_diags[:per_file_limit]:
                severity = diag.get("severity", "unknown").capitalize()
                rng = diag.get("range", {})
                start = rng.get("start", {})
                message = diag.get("message", "(no message)")
                code = diag.get("code")
                source = diag.get("source")
                location = f"L{start.get('line', '?')}:{start.get('character', '?')}"
                extra = []
                if source:
                    extra.append(str(source))
                if code:
                    extra.append(str(code))
                extra_text = f" ({', '.join(extra)})" if extra else ""
                lines.append(f"    - {severity} {location}{extra_text}: {message}")

            if len(sorted_diags) > per_file_limit:
                lines.append(f"    … {len(sorted_diags) - per_file_limit} more entries")

        return "\n".join(lines)

    def diagnostics_tool(arguments):
        payload = _parse_editor_payload(arguments)
        try:
            result = _request_editor_query("diagnostics", payload or None)
        except Exception as exc:
            return f"Diagnostics query failed: {exc}"
        return format_diagnostics(result)

    def open_editors_tool(arguments):
        try:
            result = _request_editor_query("open_editors")
        except Exception as exc:
            return f"Open editors query failed: {exc}"
        return as_json(result)

    def workspace_info_tool(arguments):
        try:
            result = _request_editor_query("workspace_info")
        except Exception as exc:
            return f"Workspace info query failed: {exc}"
        return as_json(result)

    def document_symbols_tool(arguments):
        payload = _parse_editor_payload(arguments)
        if not payload:
            payload = {}
        try:
            result = _request_editor_query("document_symbols", payload)
        except Exception as exc:
            return f"Document symbols query failed: {exc}"
        return as_json(result)

    tools["editor.diagnostics"] = {
        "run": diagnostics_tool,
        "description": "Inspect VS Code diagnostics. Args: optional JSON with path/severity/limit or a file path string.",
    }
    tools["editor.open_editors"] = {
        "run": open_editors_tool,
        "description": "List currently visible editors and selections in VS Code.",
    }
    tools["editor.workspace_info"] = {
        "run": workspace_info_tool,
        "description": "Fetch workspace folders and active file from VS Code.",
    }
    tools["editor.document_symbols"] = {
        "run": document_symbols_tool,
        "description": "List document symbols for the active file or a provided path (JSON input: {\"path\": " + "..." + "}).",
    }


def main():
    config = load_config()
    client = OpenAIClient(config)
    history = ConversationHistory()
    tools = _load_all_tools()
    _inject_editor_tools(tools)
    seed_history_with_system_prompts(history, tools)
    debug_metrics = config.get("debug_metrics", False)

    _send({"type": "ready", "debug": debug_metrics})

    while True:
        request = _next_message()
        if request is None:
            break

        action = request.get("type")
        if action in {"editor_query_response", "shell_approval_response"}:
            # Response arrived with no waiting handler; skip.
            continue
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
            _inject_editor_tools(tools)
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


        # Debug: print raw user input for tool call troubleshooting
        print(f"[DEBUG] Raw user_input: {user_input}", file=sys.stderr)
        # Check for explicit tool call in user input and return output directly (no LLM follow-up)
        tool_matches = list(TOOL_PATTERN.finditer(user_input))
        if tool_matches:
            print("[DEBUG] User tool call detected in input.", file=sys.stderr)
            tool_messages = []
            for match in tool_matches:
                tool_name = match.group(1).strip()
                tool_args = match.group(2).strip()
                print(f"[DEBUG] Executing tool: {tool_name} with args: {tool_args}", file=sys.stderr)
                if tool_name in tools:
                    try:
                        output = tools[tool_name]["run"](tool_args)
                        message = output if output else '(No output)'
                    except Exception as exc:
                        message = f"[Tool {tool_name}] Error: {exc}"
                else:
                    message = f"[Tool {tool_name}] not found."
                tool_messages.append(message)
            result = "\n".join(tool_messages)
            if not result.strip():
                _send({"type": "system", "message": "[DEBUG] Tool executed but returned empty output."})
            else:
                _send({"type": "assistant", "content": result, "debug": debug_lines})
            continue

        # Add user message, but do NOT persist router prompt or its response in history
        history.add_user_message(user_input)

        # Temporarily add router prompt for routing decision
        router_prompt = (
            "Does the following user request require a multi-step plan (tools/actions) or can it be answered directly? "
            "Reply with 'plan' or 'respond'. Request: '" + user_input + "'"
        )
        # Save current history state
        orig_history = [list(block) for block in history.memory]
        history.add_user_message(router_prompt)
        router_response, _ = _collect_response(client, history)
        decision = router_response.strip().lower()
        # Restore history to before router prompt
        history.memory = orig_history

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
            final_summary, tool_messages = _process_tool_calls(summary_response, history, client, tools, config, debug_lines, debug_metrics)
            extras_payload = aux_messages + tool_messages + ["[Chain complete. Returning to chat.]"]
            _send({
                "type": "assistant",
                "content": final_summary,
                "debug": debug_lines,
                "extras": extras_payload
            })
        else:
            direct_response, direct_elapsed = _collect_response(client, history)
            if debug_metrics:
                debug_lines.append(f"[DEBUG] Response time: {direct_elapsed:.2f}s")
            final_response, tool_messages = _process_tool_calls(direct_response, history, client, tools, config, debug_lines, debug_metrics)
            extras_payload = aux_messages + tool_messages
            _send({"type": "assistant", "content": final_response, "debug": debug_lines, "extras": extras_payload})


if __name__ == "__main__":
    main()
