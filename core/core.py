
from core.classes.Logger import Logger
logger = Logger()
logger.info("core.py started")
try:
    from core.functions._send import _send
    logger.info("imported _send")
    import re
    logger.info("imported re")
    import sys
    logger.info("imported sys")
    import time
    logger.info("imported time")
    import argparse
    logger.info("imported argparse")
    from core.classes.Memory import Memory
    logger.info("imported Memory")
    from core.functions.list_skills import list_skills
    logger.info("imported list_skills")
    from core.functions.save_skill import save_skill
    logger.info("imported save_skill")
    from core.functions.seed_history_with_system_prompts import seed_history_with_system_prompts
    logger.info("imported seed_history_with_system_prompts")
    from core.functions._load_all_tools import _load_all_tools
    logger.info("imported _load_all_tools")
    from core.functions._format_tools import _format_tools
    logger.info("imported _format_tools")
    from core.functions.core_utils import parse_editor_payload
    logger.info("imported parse_editor_payload")
    from core.functions.editor_tools import inject_editor_tools
    logger.info("imported inject_editor_tools")
    from core.functions.llm_response import collect_response, process_tool_calls
    logger.info("imported collect_response and process_tool_calls")
    from core.functions._request_editor_query import _request_editor_query  
    logger.info("imported _request_editor_query")
    from core.functions._next_message import _next_message
    logger.info("imported _next_message")
    from core.classes.Config import Config
    logger.info("imported Config")
    from core.classes.LLM import LLM
    logger.info("imported API")
except Exception as e:
    logger.error(f"Exception during imports: {e}")
    _send({"type": "error", "content": f"Exception during imports: {e}"})
    raise

TOOL_PATTERN = re.compile(r"<tool:([a-zA-Z0-9_.\-]+)>(.*?)</tool>", re.DOTALL)
_PENDING_MESSAGES = []

def main():
    try:
        logger.info("main: entered main() function")
        config = Config()
        llm = LLM(config)

        memory = Memory()
        tools = _load_all_tools()
        inject_editor_tools(tools, _request_editor_query, parse_editor_payload)
        seed_history_with_system_prompts(memory, tools)
        debug_metrics = config.get("debug_metrics", False)

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--planOnly", nargs="*", default=None)
        known_args, _ = parser.parse_known_args(sys.argv[1:])
        plan_only_args = known_args.planOnly
        if plan_only_args is not None:
            if not plan_only_args:
                print("planOnly mode requires a message.", file=sys.stderr)
                return
            plan_only_message = " ".join(plan_only_args)
            logger.info("main: running in planOnly CLI mode")
            history_snapshot = memory.snapshot()
            memory.add_user_message(plan_only_message)
            chain_limit = max(1, int(config.get("chain_limit", 25)))
            plan_prompt = (
                "Given the user's request, break it down into a numbered list of concrete steps (tools or actions) to achieve the goal. "
                f"Only plan up to {chain_limit} steps. Respond with the plan as a numbered list."
            )
            memory.add_user_message(plan_prompt)
            plan_response, plan_elapsed = collect_response(llm.client, memory, tools)
            memory.restore(history_snapshot)
            if debug_metrics:
                logger.info(f"planOnly CLI planning time: {plan_elapsed:.2f}s")
            print(plan_response)
            return

        _send({"type": "ready", "debug": debug_metrics})

        force_plan_mode = False
        while True:
            logger.info("main: waiting for next message from extension...")
            request = _next_message()
            logger.info(f"main: received message: {repr(request)}")
            if request is None:
                logger.info("main: request is None, breaking main loop")
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
                mode = request.get("mode", "default")
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
                memory = Memory()
                tools = _load_all_tools()
                inject_editor_tools(tools, _request_editor_query, parse_editor_payload)
                seed_history_with_system_prompts(memory, tools)
                aux_messages.append("[Memory cleared]")
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

            # If mode is 'plan', force planning for this request
            if mode == "plan":
                force_plan_mode = True

            if mode == "planOnly":
                history_snapshot = memory.snapshot()
                memory.add_user_message(user_input)
                chain_limit = max(1, int(config.get("chain_limit", 25)))
                plan_prompt = (
                    "Given the user's request, break it down into a numbered list of concrete steps (tools or actions) to achieve the goal. "
                    f"Only plan up to {chain_limit} steps. Respond with the plan as a numbered list."
                )
                memory.add_user_message(plan_prompt)
                plan_response, plan_elapsed = collect_response(llm.client, memory, tools)
                memory.restore(history_snapshot)
                if debug_metrics:
                    debug_lines.append(f"[DEBUG] Planning time: {plan_elapsed:.2f}s")
                _send({"type": "assistant", "content": plan_response, "debug": debug_lines, "extras": aux_messages})
                continue

            # For any mode, process LLM response for tool calls using process_tool_calls (restores shell approval logic)
            if mode in {"ask", "default", "plan"} or True:
                memory.add_user_message(user_input)
                response, elapsed = collect_response(llm.client, memory, tools)
                final_response, tool_messages = process_tool_calls(response, memory, llm.client, tools, config, debug_lines, debug_metrics)
                extras = tool_messages if tool_messages else []
                _send({"type": "assistant", "content": final_response, "debug": debug_lines, "extras": extras})
                continue
            if user_input.startswith("!run "):
                response_text = _handle_skill(user_input[5:].strip(), memory, client, tools, debug_metrics, debug_lines)
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
            memory.add_user_message(user_input)

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
                # Save current memory state
                memory_snapshot = memory.snapshot()
                memory.add_system_message(router_prompt)
                router_response, _ = collect_response(llm.client, memory, tools)
                decision = router_response.strip().lower()
                # Restore memory to before router prompt
                memory.restore(memory_snapshot)

            if "plan" in decision:
                chain_limit = max(1, int(config.get("chain_limit", 25)))
                max_step_retries = max(0, int(config.get("agent_step_retries", 2)))

                plan_prompt = (
                    "Given the user's request, break it down into a numbered list of concrete steps (tools or actions) to achieve the goal. "
                    f"Only plan up to {chain_limit} steps. Respond with the plan as a numbered list."
                )
                memory.add_user_message(plan_prompt)
                plan_response, plan_elapsed = collect_response(llm.client, memory, tools)
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

                        memory.add_user_message(execute_prompt)
                        step_response, step_elapsed = collect_response(llm.client, memory, tools)
                        if debug_metrics:
                            debug_lines.append(f"[DEBUG] Step {index} attempt {attempt_order} execution time: {step_elapsed:.2f}s")

                        step_result, step_extras = process_tool_calls(step_response, memory, llm.client, tools, config, debug_lines, debug_metrics)
                        extras_payload.extend(step_extras)
                        last_outcome = step_result

                        verification_prompt = (
                            f"Based on the recent actions and results: {last_outcome}\n"
                            f"Did this complete step {index} ('{step}')? Answer 'yes' if complete, otherwise answer 'no' and explain what remains."
                        )
                        memory.add_user_message(verification_prompt)
                        verification_response, verify_elapsed = collect_response(llm.client, memory, tools)
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
                        memory.add_user_message(
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
                memory.add_user_message(summary_prompt)
                summary_response, summary_elapsed = collect_response(llm.client, memory, tools)
                if debug_metrics:
                    debug_lines.append(f"[DEBUG] Final summary time: {summary_elapsed:.2f}s")

                final_summary, final_extras = process_tool_calls(summary_response, memory, llm.client, tools, config, debug_lines, debug_metrics)
                extras_payload.extend(final_extras)

                _send({
                    "type": "assistant",
                    "content": final_summary,
                    "debug": debug_lines,
                    "extras": extras_payload,
                })
                continue
            else:
                direct_response, direct_elapsed = collect_response(llm.client, memory, tools)
                if debug_metrics:
                    debug_lines.append(f"[DEBUG] Response time: {direct_elapsed:.2f}s")
                final_response, tool_messages = process_tool_calls(direct_response, memory, llm.client, tools, config, debug_lines, debug_metrics)
                extras_payload = aux_messages + tool_messages
                _send({"type": "assistant", "content": final_response, "debug": debug_lines, "extras": extras_payload})
    except Exception as e:
        logger.error(f"General Exception: {e}")
        _send({"type": "error", "content": f"LLM connection failed: {e}"})
        raise

if __name__ == "__main__":
    main()
