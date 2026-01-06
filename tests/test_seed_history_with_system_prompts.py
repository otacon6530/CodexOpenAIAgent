import pytest
from core.functions.seed_history_with_system_prompts import seed_history_with_system_prompts

class DummyHistory:
    def __init__(self):
        self.messages = []
    def add_system_message(self, msg):
        self.messages.append(msg)

def test_seed_history_with_system_prompts_agent_md(monkeypatch):
    h = DummyHistory()
    # agent_md returns None
    import core.functions.seed_history_with_system_prompts as mod
    monkeypatch.setattr(mod, "load_agent_markdown", lambda x: None)
    seed_history_with_system_prompts(h, {"foo": {"description": "bar"}})
    # Should have 1 message (os), not agent_md or tools
    assert len(h.messages) == 1

def test_seed_history_with_system_prompts_agent_md_present(monkeypatch):
    h = DummyHistory()
    import core.functions.seed_history_with_system_prompts as mod
    monkeypatch.setattr(mod, "load_agent_markdown", lambda x: "AGENT")
    seed_history_with_system_prompts(h, {"foo": {"description": "bar"}})
    # Should have 3 messages (os, agent_md, tools)
    assert any(m == "AGENT" for m in h.messages)

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
