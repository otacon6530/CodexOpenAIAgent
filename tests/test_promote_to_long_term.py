from core.functions.promote_to_long_term import promote_to_long_term

from collections import defaultdict

def test_promote_to_long_term_basic():
    # Minimal smoke test
    called = {"called": False}
    def fake_append(msgs):
        called["called"] = True
    def fake_is_turn_in_window(turn_id):
        return False
    evicted = defaultdict(list)
    message = {"metadata": {"turn_id": 1}}
    promote_to_long_term(message, evicted, fake_is_turn_in_window, fake_append)
    assert called["called"]
