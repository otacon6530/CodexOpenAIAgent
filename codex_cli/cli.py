from .api import OpenAIClient
from .history import ConversationHistory
from .config import load_config
from .tool_loader import load_tools
from .mcp_tools import discover_mcp_tools, run_mcp_tool
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.styles import Style
import sys
import argparse
import re
import threading
import queue
import os

def build_tools_prompt(tools):
    lines = ["Available tools:"]
    for name, t in tools.items():
        lines.append(f"- {name}: {t['description']}")
    lines.append("To call a tool, reply with <tool:name>args</tool>.")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="codex-cli: LLM chat and exec tool")
    parser.add_argument('--exec', dest='exec_message', type=str, help='Send a single message and print the response, then exit')
    args = parser.parse_args()

    config = load_config()
    client = OpenAIClient(config)
    history = ConversationHistory()

    # Load local tools
    tools = load_tools()
    # Load MCP tools
    mcp_tools = discover_mcp_tools()
    # Add MCP tools to the tool list (with a marker)
    for name, desc in mcp_tools.items():
        tools[name] = {
            'run': lambda args, n=name: run_mcp_tool(n, args),
            'description': f'(MCP) {desc}'
        }

    # Add OS info and tool list to system prompt as system messages
    import platform
    os_info = platform.system()
    os_message = f"You are running in a {os_info} environment. Use appropriate shell commands for this OS."
    history.add_system_message(os_message)
    system_prompt = build_tools_prompt(tools)
    history.add_system_message(system_prompt)

    if args.exec_message:
        if args.exec_message.startswith('!'):
            # Tool call: !toolname args
            parts = args.exec_message[1:].split(maxsplit=1)
            toolname = parts[0]
            toolarg = parts[1] if len(parts) > 1 else ''
            if toolname in tools:
                print(tools[toolname]['run'](toolarg))
            else:
                print(f"Tool '{toolname}' not found.")
            return
        history.add_user_message(args.exec_message)
        for chunk in client.stream_chat(history.get_messages()):
            print(chunk, end="", flush=True)
        print()
        return

    tool_pattern = re.compile(r'<tool:(\w+)>(.*?)</tool>', re.DOTALL)
    session = PromptSession()
    style = Style.from_dict({
        'user': 'ansicyan',
        'assistant': 'ansiyellow',
        'tool': 'ansigreen',
    })
    chat_log = []

    import shutil
    def print_chat_log_bottom(chat_log, style):
        # Get terminal height
        try:
            height = shutil.get_terminal_size().lines
        except Exception:
            height = 24
        # Number of lines in chat log
        chat_lines = sum(msg[1].count('\n') + 1 for msg in chat_log)
        pad_lines = max(0, height - chat_lines - 2)  # -2 for prompt and buffer
        # Print blank lines above the chat log to fill space
        if pad_lines > 0:
            print('\n' * pad_lines, end='')
        print_formatted_text(FormattedText(chat_log), style=style)

    print("codex-cli (type 'exit' to quit)")
    with patch_stdout():
        while True:
            try:
                # Clear the prompt_toolkit screen before rendering chat log
                session.app.renderer.clear()
                # Use custom print function to bottom-align chat
                print_chat_log_bottom(chat_log, style)
                user_input = session.prompt([('class:user', 'You: ')], refresh_interval=0.1)
                if user_input.lower() in ("exit", "quit"): break
                if not user_input: continue
                if user_input == '!tools':
                    tool_lines = [('', 'Available tools:')]
                    for name, t in tools.items():
                        tool_lines.append(('class:tool', f'- {name}: {t["description"]}'))
                    chat_log.extend(tool_lines)
                    print_chat_log_bottom(chat_log, style)
                    continue
                if user_input == '!new':
                    history = ConversationHistory()
                    # Re-add OS info and reload tools (including MCP)
                    import platform
                    os_info = platform.system()
                    os_message = f"You are running in a {os_info} environment. Use appropriate shell commands for this OS."
                    history.add_system_message(os_message)
                    # Reload local and MCP tools
                    tools.clear()
                    tools.update(load_tools())
                    mcp_tools = discover_mcp_tools()
                    for name, desc in mcp_tools.items():
                        tools[name] = {
                            'run': lambda args, n=name: run_mcp_tool(n, args),
                            'description': f'(MCP) {desc}'
                        }
                    system_prompt = build_tools_prompt(tools)
                    history.add_system_message(system_prompt)
                    chat_log = []
                    chat_log.append(('', '[History cleared]'))
                    print_chat_log_bottom(chat_log, style)
                    continue
                if user_input.startswith('!'):
                    parts = user_input[1:].split(maxsplit=1)
                    toolname = parts[0]
                    toolarg = parts[1] if len(parts) > 1 else ''
                    if toolname in tools:
                        tool_result = tools[toolname]['run'](toolarg)
                        chat_log.append(('class:tool', tool_result))
                    else:
                        chat_log.append(('class:tool', f"Tool '{toolname}' not found."))
                    print_chat_log_bottom(chat_log, style)
                    continue
                # Only add non-empty, non-system-prompt user messages
                if user_input.strip() and user_input != system_prompt:
                    history.add_user_message(user_input)
                    chat_log.append(('class:user', f'You: {user_input}\n'))
                    response = ""
                    for chunk in client.stream_chat(history.get_messages()):
                        response += chunk
                    # Remove tool call tags from assistant output
                    clean_response = tool_pattern.sub("", response)
                    chat_log.append(('class:assistant', f'Assistant: {clean_response.strip()}\n'))
                    # Tool call detection
                    match = tool_pattern.search(response)
                    if match:
                        toolname, toolarg = match.group(1), match.group(2).strip()
                        if toolname in tools:
                            tool_result = tools[toolname]['run'](toolarg)
                            chat_log.append(('class:tool', tool_result))
                        else:
                            chat_log.append(('class:tool', f"Tool '{toolname}' not found."))
                    assistant_reply = client.get_last_response()
                    history.add_assistant_message(assistant_reply)
                    print_chat_log_bottom(chat_log, style)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break


if __name__ == "__main__":
    main()
