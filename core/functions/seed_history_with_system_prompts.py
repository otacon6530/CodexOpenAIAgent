from core.functions.build_os_message import build_os_message
from core.functions.load_agent_markdown import load_agent_markdown
from core.functions.build_tools_prompt import build_tools_prompt

def seed_history_with_system_prompts(history, tools, search_dirs=None):
    history.add_system_message(build_os_message())
    agent_md = load_agent_markdown(search_dirs)
    if agent_md:
        history.add_system_message(agent_md)
    history.add_system_message(build_tools_prompt(tools))
