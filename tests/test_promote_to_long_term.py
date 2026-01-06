import pytest
from core.functions.promote_to_long_term import promote_to_long_term

def test_promote_to_long_term_no_turn_id():
    called = {"called": False}
    def append_long_term_entry(msgs):
        called["called"] = True
        assert isinstance(msgs, list)
    promote_to_long_term({"metadata": {}}, {}, lambda tid: True, append_long_term_entry)
    assert called["called"]

def test_promote_to_long_term_buffered():
    from collections import defaultdict
    evicted = defaultdict(list)
    called = {"called": False, "msgs": None}
    def append_long_term_entry(msgs):
        called["called"] = True
        called["msgs"] = msgs
    # turn_id present, not in window, buffer is empty, so append is called immediately
    promote_to_long_term({"metadata": {"turn_id": 1}}, evicted, lambda tid: False, append_long_term_entry)
    assert called["called"]

def test_promote_to_long_term_in_window():
    from collections import defaultdict
    evicted = defaultdict(list)
    called = {"called": False}
    def append_long_term_entry(msgs):
        called["called"] = True
    # turn_id present, in window, should not call append
    promote_to_long_term({"metadata": {"turn_id": 2}}, evicted, lambda tid: True, append_long_term_entry)
    assert not called["called"]
    called = {"called": False}
    def fake_append(msgs):
        called["called"] = True
    def fake_is_turn_in_window(turn_id):
        return False
    evicted = defaultdict(list)
    message = {"metadata": {"turn_id": 1}}
    promote_to_long_term(message, evicted, fake_is_turn_in_window, fake_append)
    assert called["called"]
