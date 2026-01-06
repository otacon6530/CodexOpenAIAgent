from core.functions.seed_history_with_system_prompts import seed_history_with_system_prompts

class SystemPrompt:
    def seed(self, history, tools, search_dirs=None):
        return seed_history_with_system_prompts(history, tools, search_dirs)
