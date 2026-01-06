import json
from core.classes.Logger import Logger
logger = Logger()
logger.info("core.py started")
import re
import sys
import time

from core.functions.openai_client import OpenAIClient
from core.functions.load_config import load_config
from core.classes.History import History
from core.functions.discover_mcp_tools import discover_mcp_tools
from core.functions.run_mcp_tool import run_mcp_tool
from core.functions.list_skills import list_skills
from core.functions.load_skill import load_skill
from core.functions.save_skill import save_skill
from core.functions.seed_history_with_system_prompts import seed_history_with_system_prompts
from core.functions.load_tools import load_tools

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
    # Only include system/tool instructions once, and last 3 turns for efficiency
    from core.functions.build_tools_prompt import build_tools_prompt
    tool_instructions = build_tools_prompt(load_tools())
    if not hasattr(history, "get_efficient_prompt"):
        raise AttributeError("History object must implement get_efficient_prompt in production.")
    messages = history.get_efficient_prompt(include_system=True, recent_turns=3, tool_instructions=tool_instructions)
    # Strip metadata from log (should already be stripped, but double-sanitize for safety)
    log_prompt = [
        {k: v for k, v in m.items() if k in ("role", "content")} for m in messages
    ]
    logger.info(f"LLM PROMPT: {json.dumps(log_prompt)}")
    for chunk in client.stream_chat(messages):
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

    llm_summaries = []
    first_tool_output = None
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
                    message = output if output else '(No output)'
                    if first_tool_output is None:
                        first_tool_output = message
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
        llm_summaries.append(followup_response.strip())
        text = followup_response.strip()
        if debug_metrics:
            debug_lines.append(f"[DEBUG] Tool follow-up time: {followup_elapsed:.2f}s")

    cleaned = TOOL_PATTERN.sub('', text)
    # Prioritize tool output as main message, append LLM summary as extras
    main_message = first_tool_output if first_tool_output is not None else cleaned
    extras = tool_messages + llm_summaries
    return main_message, extras


def _send(payload):
    try:
        debug_message = json.dumps(payload)
    except Exception:
        debug_message = str(payload)
    logger.info(f"SEND: {debug_message}")
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
            msg = json.loads(line)
            logger.info(f"RECEIVE: {json.dumps(msg)}")
            return msg
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
        logger.info(f"RECEIVE (buffered): {json.dumps(buffered)}")
        return buffered
    return _read_raw_message()


def _wait_for_message(expected_type, expected_id=None, timeout=None):
    if expected_type is None:
        raise ValueError("expected_type is required")

    deadline = time.time() + timeout if timeout else None

    buffered = _pop_buffered_message(expected_type, expected_id)
    if buffered is not None:
        logger.info(f"RECEIVE (wait/buffered): {json.dumps(buffered)}")
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
    from core.classes.Config import Config
    config = Config()
    client = OpenAIClient(config)
    history = History()
    tools = _load_all_tools()
    _inject_editor_tools(tools)
    seed_history_with_system_prompts(history, tools)
    debug_metrics = config.get("debug_metrics", False)

    _send({"type": "ready", "debug": debug_metrics})


    force_plan_mode = False
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
            _send({"type": "notification", "content": f"Debug metrics {'enabled' if debug_metrics else 'disabled' }.", "debug": debug_metrics})
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
            history = History()
            tools = _load_all_tools()
            _inject_editor_tools(tools)
            seed_history_with_system_prompts(history, tools)
            aux_messages.append("[History cleared]")
            _send({"type": "assistant", "content": "\n".join(aux_messages), "debug": debug_lines})
            continue
        if user_input == "!debug":
            debug_metrics = not debug_metrics
            _send({"type": "notification", "content": f"Debug metrics {'enabled' if debug_metrics else 'disabled' }.", "debug": debug_metrics})
            continue
        # Handle /plan as a special command to force planning for the current request
        if user_input.strip().lower().startswith("/plan"):
            # Extract the actual user request after /plan
            user_input = user_input[len("/plan"):].strip()
            force_plan_mode = True
            # If nothing follows /plan, prompt for input
            if not user_input:
                _send({"type": "assistant", "content": "[Force planning mode enabled for next request. Please enter your request after /plan.]"})
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

        # If force_plan_mode is set, skip router and force planning
        if force_plan_mode:
            decision = "plan"
            force_plan_mode = False
        else:
            # Improved router prompt for plan/respond decision as a system message
            router_prompt = (
                "You are an AI assistant that can either answer questions directly or plan multi-step solutions using available tools.\n"
                "For the following user request, decide if it requires multi-step planning (using tools or actions in sequence) or if you can answer it directly.\n"
                "- If the request is simple (e.g., 'What is 2+2?' or 'What’s the weather?'), reply with: respond\n"
                "- If the request requires multiple steps, tool use, or actions (e.g., 'Create a file and then summarize its contents'), reply with: plan\n"
                f"User request: '{user_input}'\n"
                "Reply with only one word: plan or respond"
            )
            # Save current history state
            history_snapshot = history.snapshot()
            history.add_system_message(router_prompt)
            router_response, _ = _collect_response(client, history)
            decision = router_response.strip().lower()
            # Restore history to before router prompt
            history.restore(history_snapshot)

        if "plan" in decision:
            chain_limit = max(1, int(config.get("chain_limit", 25)))
            max_step_retries = max(0, int(config.get("agent_step_retries", 2)))

            plan_prompt = (
                "Given the user's request, break it down into a numbered list of concrete steps (tools or actions) to achieve the goal. "
                f"Only plan up to {chain_limit} steps. Respond with the plan as a numbered list."
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

            extras_payload = list(aux_messages)
            step_records = []
            start_time = time.time()

            for index, step in enumerate(steps[:chain_limit], start=1):
                extras_payload.append(f"[Plan Step {index}] {step}")
                attempt = 0
                attempt_count = 0
                feedback = ""
                last_outcome = ""
                verification_text = ""
                step_complete = False

                while attempt <= max_step_retries:
                    attempt_order = attempt + 1
                    execute_prompt = (
                        f"Execute step {index}: '{step}'. "
                        "Use tools when needed by returning <tool:name>arguments</tool>. "
                        "Provide clear results of your actions."
                    )
                    if feedback:
                        execute_prompt += f" Previous feedback: {feedback}"

                    history.add_user_message(execute_prompt)
                    step_response, step_elapsed = _collect_response(client, history)
                    if debug_metrics:
                        debug_lines.append(f"[DEBUG] Step {index} attempt {attempt_order} execution time: {step_elapsed:.2f}s")

                    step_result, step_extras = _process_tool_calls(step_response, history, client, tools, config, debug_lines, debug_metrics)
                    extras_payload.extend(step_extras)
                    last_outcome = step_result

                    verification_prompt = (
                        f"Based on the recent actions and results: {last_outcome}\n"
                        f"Did this complete step {index} ('{step}')? Answer 'yes' if complete, otherwise answer 'no' and explain what remains."
                    )
                    history.add_user_message(verification_prompt)
                    verification_response, verify_elapsed = _collect_response(client, history)
                    if debug_metrics:
                        debug_lines.append(f"[DEBUG] Step {index} attempt {attempt_order} verification time: {verify_elapsed:.2f}s")

                    verification_text = verification_response.strip()
                    normalized_verification = verification_text.lower()
                    attempt_count = attempt_order
                    if normalized_verification.startswith("yes"):
                        step_complete = True
                        extras_payload.append(f"[Step {index}] Completed in {attempt_order} attempt(s).")
                        break

                    extras_payload.append(
                        f"[Step {index}] Attempt {attempt_order} incomplete: {verification_text.splitlines()[0]}"
                    )
                    feedback = verification_text
                    attempt += 1
                    if attempt > max_step_retries:
                        break
                    history.add_user_message(
                        f"Step '{step}' remains incomplete. Adjust your approach using this feedback: {feedback}. Then try again."
                    )

                step_records.append({
                    "index": index,
                    "step": step,
                    "completed": step_complete,
                    "attempts": attempt_count or (attempt + 1),
                    "result": last_outcome,
                    "verification": verification_text or feedback,
                })

                if not step_complete:
                    extras_payload.append(
                        f"[Step {index}] Failed after {attempt_count or (attempt + 1)} attempt(s). Latest outcome: {last_outcome or '(no result)'}"
                    )

            elapsed_time = time.time() - start_time
            if debug_metrics:
                debug_lines.append(
                    f"[DEBUG] Agentic planning steps executed: {len(step_records)} | Total time: {elapsed_time:.2f}s"
                )

            step_summaries = "\n".join(
                [
                    f"Step {record['index']}: {record['step']} -> {'complete' if record['completed'] else 'incomplete'}"
                    f" | Attempts: {record['attempts']}"
                    f" | Result: {record['result']}"
                    for record in step_records
                ]
            )

            summary_prompt = (
                f"Goal: '{user_input}'.\n"
                "Provide a final user-facing summary that explains the work completed, mentions any remaining tasks, and confirms whether the goal is satisfied.\n"
                "Here are the step outcomes:\n"
                f"{step_summaries}\n"
                "Respond concisely for the user."
            )
            history.add_user_message(summary_prompt)
            summary_response, summary_elapsed = _collect_response(client, history)
            if debug_metrics:
                debug_lines.append(f"[DEBUG] Final summary time: {summary_elapsed:.2f}s")

            final_summary, final_extras = _process_tool_calls(summary_response, history, client, tools, config, debug_lines, debug_metrics)
            extras_payload.extend(final_extras)

            _send({
                "type": "assistant",
                "content": final_summary,
                "debug": debug_lines,
                "extras": extras_payload,
            })
            continue
        else:
            direct_response, direct_elapsed = _collect_response(client, history)
            if debug_metrics:
                debug_lines.append(f"[DEBUG] Response time: {direct_elapsed:.2f}s")
            final_response, tool_messages = _process_tool_calls(direct_response, history, client, tools, config, debug_lines, debug_metrics)
            extras_payload = aux_messages + tool_messages
            _send({"type": "assistant", "content": final_response, "debug": debug_lines, "extras": extras_payload})


if __name__ == "__main__":
    main()
