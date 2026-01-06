from core.history import ConversationHistory

class History:
    def __init__(self, *args, **kwargs):
        self.history = ConversationHistory(*args, **kwargs)

    def add_system_message(self, *args, **kwargs):
        return self.history.add_system_message(*args, **kwargs)

    def add_user_message(self, *args, **kwargs):
        return self.history.add_user_message(*args, **kwargs)

    def add_assistant_message(self, *args, **kwargs):
        return self.history.add_assistant_message(*args, **kwargs)

    def get_messages(self, *args, **kwargs):
        return self.history.get_messages(*args, **kwargs)

    def get_long_term_context(self, *args, **kwargs):
        return self.history.get_long_term_context(*args, **kwargs)

    def get_running_summary(self):
        return self.history.get_running_summary()

    def snapshot(self):
        return self.history.snapshot()

    def restore(self, snapshot):
        return self.history.restore(snapshot)
