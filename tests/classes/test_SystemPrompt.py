from core.classes.SystemPrompt import SystemPrompt

class DummyHistory:
    def __init__(self):
        self.messages = []
    def add_system_message(self, msg):
        self.messages.append(msg)

def test_seed():
    def fake_seed_func(h, t, s=None):
        return "seeded"
    sp = SystemPrompt(seed_func=fake_seed_func)
    dummy_history = DummyHistory()
    assert sp.seed(dummy_history, {}) == "seeded"
