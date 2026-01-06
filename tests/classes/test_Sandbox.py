from core.classes.Sandbox import Sandbox

def test_is_safe_path():
    s = Sandbox(safe_path_func=lambda p: p == "safe")
    assert s.is_safe_path("safe")
    assert not s.is_safe_path("unsafe")
