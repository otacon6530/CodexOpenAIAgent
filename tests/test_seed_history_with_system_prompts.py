from core.functions.seed_history_with_system_prompts import seed_history_with_system_prompts

class DummyHistory:
    def __init__(self):
        self.messages = []
    def add_system_message(self, msg):
        self.messages.append(msg)

def test_seed_history_with_system_prompts():
    h = DummyHistory()
    seed_history_with_system_prompts(h, {"foo": {"description": "bar"}})
    assert any("environment" in m for m in h.messages)
    assert any("Available tools" in m for m in h.messages)
