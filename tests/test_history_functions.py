import pytest
from core.functions import history_functions

def test_default_token_estimator():
    assert history_functions.default_token_estimator("") == 0
    assert history_functions.default_token_estimator("hello world") > 0

def test_default_token_estimator_edge():
    # Only whitespace
    assert history_functions.default_token_estimator("   ") == 0

def test_shorten():
    assert history_functions.shorten("abc", 5) == "abc"
    assert history_functions.shorten("abcdef", 5).endswith("...")

def test_make_entry_metadata():
    meta = history_functions.make_entry_metadata("hi", ["t1"], {"foo":1}, 2, lambda x: 5)
    assert meta["tokens"] == 5
    assert meta["topics"] == ["t1"]
    assert meta["foo"] == 1
    assert meta["turn_id"] == 2

def test_make_entry_metadata_no_topics_no_meta_no_turn():
    meta = history_functions.make_entry_metadata("hi", None, None, None, lambda x: 1)
    assert meta["tokens"] == 1
    assert "topics" not in meta
    assert "turn_id" not in meta

def test_promote_to_long_term():
    called = {"called": False}
    def append(msgs):
        called["called"] = True
    history_functions.promote_to_long_term({"metadata": {}}, {}, lambda tid: True, append)
    assert called["called"]

def test_append_long_term_entry():
    ltc = []
    called = {"called": False}
    def refresh():
        called["called"] = True
    msgs = [
        {"role": "user", "content": "hi", "metadata": {"turn_id": 1, "topics": ["t"]}},
        {"role": "assistant", "content": "hello", "metadata": {"turn_id": 1}},
        {"role": "other", "content": "zzz", "metadata": {"turn_id": 1}},
    ]
    history_functions.append_long_term_entry(msgs, ltc, 2, lambda x: 1, refresh)
    assert ltc
    assert called["called"]
    # Test max_long_term_entries
    history_functions.append_long_term_entry(msgs, ltc, 1, lambda x: 1, refresh)
    assert len(ltc) == 1
    # Test empty messages
    history_functions.append_long_term_entry([], ltc, 1, lambda x: 1, refresh)

def test_append_long_term_entry_roles():
    ltc = []
    called = {"called": False}
    def refresh():
        called["called"] = True
    msgs = [
        {"role": "other", "content": "zzz", "metadata": {"turn_id": 1}},
    ]
    history_functions.append_long_term_entry(msgs, ltc, 2, lambda x: 1, refresh)
    assert ltc
    assert called["called"]
