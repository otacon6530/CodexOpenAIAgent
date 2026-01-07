from core.functions.load_agent_markdown import load_agent_markdown

def seed_history_with_system_prompts(history, tools, search_dirs=None):
    agent_md = load_agent_markdown(search_dirs)
    if agent_md:
        history.add_system_message(agent_md)
    