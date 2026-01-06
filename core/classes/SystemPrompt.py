from core.functions.seed_history_with_system_prompts import seed_history_with_system_prompts

class SystemPrompt:
    def __init__(self, seed_func=None):
        self._seed_func = seed_func or seed_history_with_system_prompts

    def seed(self, history, tools, search_dirs=None):
        return self._seed_func(history, tools, search_dirs)
