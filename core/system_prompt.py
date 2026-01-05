import glob
import os
import platform

from typing import Iterable, Mapping, Optional


def build_tools_prompt(tools: Mapping[str, dict]) -> str:
    lines = ["Available tools:"]
    for name, tool in tools.items():
        description = tool.get("description", "")
        # Add example for create_file tool
        if name == "create_file":
            description += " Example: <tool:create_file>test.txt|hello world</tool> creates test.txt with 'hello world'. Prefer this over shell commands for file creation."
        lines.append(f"- {name}: {description}")
    lines.append("To call a tool, reply with <tool:name>args</tool>.")
    return "\n".join(lines)


def load_agent_markdown(search_dirs: Optional[Iterable[str]] = None) -> Optional[str]:
    if search_dirs is None:
        cwd = os.getcwd()
        search_dirs = [cwd, os.path.join(cwd, "cli")]
    for directory in search_dirs:
        try:
            for path in glob.glob(os.path.join(directory, "*.[mM][dD]")):
                if os.path.basename(path).lower() == "agent.md":
                    with open(path, "r", encoding="utf-8") as handle:
                        return handle.read()
        except Exception:
            continue
    return None


def build_os_message() -> str:
    return f"You are running in a {platform.system()} environment. Use appropriate shell commands for this OS."


def seed_history_with_system_prompts(history, tools, search_dirs: Optional[Iterable[str]] = None) -> None:
    history.add_system_message(build_os_message())
    agent_md = load_agent_markdown(search_dirs)
    if agent_md:
        history.add_system_message(agent_md)
    history.add_system_message(build_tools_prompt(tools))
