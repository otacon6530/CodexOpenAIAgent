# LLM response collection and tool call processing from core/core.py
import time
import json
import sys
from core.functions.build_tools_prompt import build_tools_prompt


def collect_response(client, history, tools, on_chunk=None):
    start = time.time()
    response = ""
    tool_instructions = build_tools_prompt(tools)
    if not hasattr(history, "get_efficient_prompt"):
        raise AttributeError("History object must implement get_efficient_prompt in production.")
    messages = history.get_efficient_prompt(include_system=True, recent_turns=3, tool_instructions=tool_instructions)
    log_prompt = [
        {k: v for k, v in m.items() if k in ("role", "content")} for m in messages
    ]
    from core.classes.Logger import Logger
    logger = Logger()
    logger.info(f"LLM PROMPT: {json.dumps(log_prompt)}")
    for chunk in client.stream_chat(messages):
        response += chunk
        if on_chunk:
            on_chunk(chunk)
    elapsed = time.time() - start
    return response, elapsed

def process_tool_calls(response_text, history, client, tools, config, debug_lines, debug_metrics):
    import re
    from core.classes.Logger import Logger
    logger = Logger()
    try:
        TOOL_PATTERN = re.compile(r"<tool:([a-zA-Z0-9_.\-]+)>(.*?)</tool>", re.DOTALL)
        max_iterations = max(1, int(config.get("tool_iterations", 3)))
        tool_messages = []
        text = response_text.strip()
        iterations = 0
        shell_approve_all = getattr(process_tool_calls, "shell_approve_all", False)
        shell_approval_cache = getattr(process_tool_calls, "shell_approval_cache", {})
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
            logger.info(f"process_tool_calls: found {len(matches)} tool matches in response text.")
            if not matches:
                break
            if iterations >= max_iterations:
                tool_messages.append("[Tool execution limit reached]")
                break
            iterations += 1
            for match in matches:
                tool_name = match.group(1).strip()
                tool_args = match.group(2).strip()
                logger.info(f"process_tool_calls: tool_name={tool_name}, tool_args={tool_args}")
                if tool_name == "shell":
                    if not shell_approve_all:
                        cache_key = tool_args.strip()
                        if cache_key in shell_approval_cache:
                            approved, approve_all = shell_approval_cache[cache_key]
                        else:
                            approved, approve_all = request_shell_approval(tool_args)
                            shell_approval_cache[cache_key] = (approved, approve_all)
                        if approve_all:
                            shell_approve_all = True
                            process_tool_calls.shell_approve_all = True
                        if not approved:
                            message = f"[Tool shell] Command denied by user."
                            history.add_system_message(message)
                            tool_messages.append(message)
                            continue
                if tool_name in tools:
                    try:
                        logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                        output = tools[tool_name]["run"](tool_args)
                        logger.info(f"Tool {tool_name} output: {output}")
                        if output:
                            message = output
                            if first_tool_output is None:
                                first_tool_output = message
                            history.add_system_message(message)
                            tool_messages.append(message)
                    except Exception as exc:
                        logger.error(f"Tool {tool_name} error: {exc}")
                        message = f"[Tool {tool_name}] Error: {exc}"
                        history.add_system_message(message)
                        tool_messages.append(message)
                else:
                    message = f"[Tool {tool_name}] not found."
                    history.add_system_message(message)
                    tool_messages.append(message)
                if debug_metrics:
                    preview = tool_args[:40] + ("…" if len(tool_args) > 40 else "")
                    debug_lines.append(f"[DEBUG] Tool {tool_name} invoked with args: {preview}")
            history.add_user_message("Please summarize or explain the result of the previous tool call for the user.")
            followup_response, followup_elapsed = collect_response(client, history, tools)
            llm_summaries.append(followup_response.strip())
            text = followup_response.strip()
            if debug_metrics:
                debug_lines.append(f"[DEBUG] Tool follow-up time: {followup_elapsed:.2f}s")
        cleaned = TOOL_PATTERN.sub('', text)
        main_message = text if text else (first_tool_output if first_tool_output is not None else cleaned)
        extras = tool_messages + llm_summaries
        return main_message, extras
    except Exception as e:
        logger.error(f"process_tool_calls: Exception occurred: {e}")
        return f"[ERROR] process_tool_calls failed: {e}", []

def _send(payload):
    try:
        debug_message = json.dumps(payload)
    except Exception:
        debug_message = str(payload)
    # logger.info(f"SEND: {debug_message}")
    print(f"[DEBUG] Sending to extension: {debug_message}", file=sys.stderr)
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()

def _wait_for_message(expected_type, expected_id=None, timeout=None):
    import time
    deadline = time.time() + timeout if timeout else None
    while True:
        if deadline is not None and time.time() > deadline:
            return None
        # This should be replaced with the actual message reading logic from your main loop
        return None  # Placeholder
