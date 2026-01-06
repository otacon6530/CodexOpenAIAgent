from core.functions.seed_history_with_system_prompts import seed_history_with_system_prompts

class DummyHistory:
    def __init__(self):
        self.messages = []
    def add_system_message(self, msg):
        self.messages.append(msg)

def test_seed_history_with_system_prompts():
    h = DummyHistory()
    # Normal tools
    seed_history_with_system_prompts(h, {"foo": {"description": "bar"}})
    assert any("environment" in m for m in h.messages)
    assert any("Available tools" in m for m in h.messages)

    # Empty tools
    h2 = DummyHistory()
    seed_history_with_system_prompts(h2, {})
    assert any("environment" in m for m in h2.messages)

    # With search_dirs (should not error)
    h3 = DummyHistory()
    seed_history_with_system_prompts(h3, {"foo": {"description": "bar"}}, search_dirs=["."])
    assert any("environment" in m for m in h3.messages)

    # Malformed history (missing add_system_message)
    class BadHistory:
        pass
    bad = BadHistory()
    try:
        seed_history_with_system_prompts(bad, {"foo": {"description": "bar"}})
    except AttributeError:
        pass
    else:
        assert False, "Should raise AttributeError for missing add_system_message"
