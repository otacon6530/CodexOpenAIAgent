def test_append_long_term_entry_empty():
    long_term_context = []
    called = {"refreshed": False}
    def fake_refresh():
        called["refreshed"] = True
    append_long_term_entry([], long_term_context, 10, lambda x: 1, fake_refresh)
    assert long_term_context == []
    assert not called["refreshed"]

def test_append_long_term_entry_truncates():
    long_term_context = []
    called = {"refreshed": False}
    def fake_refresh():
        called["refreshed"] = True
    for i in range(15):
        messages = [
            {"role": "user", "content": f"msg {i}", "metadata": {"turn_id": i}},
        ]
        append_long_term_entry(messages, long_term_context, 5, lambda x: 1, fake_refresh)
    assert len(long_term_context) == 5
import pytest
from core.functions.append_long_term_entry import append_long_term_entry

def test_append_long_term_entry_basic():
    messages = [
        {"role": "user", "content": "Hello", "metadata": {"turn_id": 1, "topics": ["greet"]}},
        {"role": "assistant", "content": "Hi!", "metadata": {"turn_id": 1, "topics": ["greet"]}},
        {"role": "system", "content": "System note", "metadata": {"turn_id": 1, "topics": ["meta"]}},
    ]
    long_term_context = []
    called = {"refreshed": False}
    def fake_refresh():
        called["refreshed"] = True
    append_long_term_entry(messages, long_term_context, 10, lambda x: 1, fake_refresh)
    assert len(long_term_context) == 1
    entry = long_term_context[0]
    assert called["refreshed"]
    assert "summary" in entry
    assert "User: Hello" in entry["summary"]
    assert "Assistant: Hi!" in entry["summary"]
    assert "system: system note" in entry["summary"].lower()
    assert entry["turn_ids"] == [1]
    assert set(entry["topics"]) == {"greet", "meta"}
    assert "timestamp" in entry

def test_append_long_term_entry_other_role():
    messages = [
        {"role": "other", "content": "zzz", "metadata": {"turn_id": 3}}
    ]
    long_term_context = []
    called = {"refreshed": False}
    def fake_refresh():
        called["refreshed"] = True
    append_long_term_entry(messages, long_term_context, 10, lambda x: 1, fake_refresh)
    assert "other" in long_term_context[-1]["summary"].lower()
    assert called["refreshed"]
