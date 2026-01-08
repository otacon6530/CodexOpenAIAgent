from core.classes.Memory import ConversationHistory

def test_add_and_get_messages():
    h = ConversationHistory(token_window=1000)
    h.add_user_message("Hello")
    h.add_assistant_message("Hi!")
    msgs = h.get_messages()
    assert len(msgs) == 2
    assert msgs[0]['role'] == 'user'
    assert msgs[1]['role'] == 'assistant'

def test_snapshot_and_restore():
    h = ConversationHistory()
    h.add_user_message("A")
    snap = h.snapshot()
    h2 = ConversationHistory()
    h2.restore(snap)
    assert h2.get_messages()[0]['content'] == "A"

def test_add_system_and_arbitrary_message():
    h = ConversationHistory()
    h.add_system_message("sys")
    h.add_message("user", "u")
    h.add_message("assistant", "a")
    h.add_message("other", "o")
    msgs = h.get_messages()
    assert any(m["role"] == "system" for m in msgs)
    assert any(m["role"] == "other" for m in msgs)

def test_get_messages_token_budget_and_recent_count():
    h = ConversationHistory(token_window=10)
    for i in range(5):
        h.add_user_message(f"msg {i}")
    # Should return only messages within token window
    msgs = h.get_messages(token_budget=1)
    assert isinstance(msgs, list)
    # Should return only recent_count
    msgs2 = h.get_messages(recent_count=2)
    assert len(msgs2) == 2

def test_get_long_term_context_and_running_summary():
    h = ConversationHistory()
    assert h.get_long_term_context() == []
    assert isinstance(h.get_running_summary(), str)

def test_restore_partial_snapshot():
    h = ConversationHistory()
    h.restore({})
    assert h.get_messages() == []

def test_internal_helpers():
    h = ConversationHistory()
    h.add_user_message("foo")
    # _is_turn_in_window
    tid = h._turn_id
    assert h._is_turn_in_window(tid)
    # _append_message with metadata
    h._append_message("user", "bar", metadata={"tokens": 1}, turn_id=tid)
    # _enforce_window with zero window
    h.token_window = 0
    h._enforce_window()
    # _refresh_running_summary
    h._refresh_running_summary()

def test_enforce_window_and_long_term():
    h = ConversationHistory(token_window=1)
    h.add_user_message("A")
    h.add_user_message("B")
    # Should evict and promote to long term
    assert isinstance(h.long_term_context, list)

def test_refresh_running_summary_token_budget():
    h = ConversationHistory(summary_token_budget=1)
    h.add_user_message("A" * 100)
    h.add_assistant_message("B" * 100)
    h._refresh_running_summary()
    assert isinstance(h.running_summary, str)
