import pytest
from core.functions.append_long_term_entry import append_long_term_entry

def test_append_long_term_entry_basic():
    # Minimal smoke test for append_long_term_entry
    messages = [
        {"role": "user", "content": "Hello", "metadata": {"turn_id": 1}},
        {"role": "assistant", "content": "Hi!", "metadata": {"turn_id": 1}},
    ]
    long_term_context = []
    called = {"refreshed": False}
    def fake_refresh():
        called["refreshed"] = True
    append_long_term_entry(messages, long_term_context, 10, lambda x: 1, fake_refresh)
    assert len(long_term_context) == 1
    assert called["refreshed"]
    assert "summary" in long_term_context[0]
