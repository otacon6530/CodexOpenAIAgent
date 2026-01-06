from core.functions.is_safe_path import is_safe_path
import os

def test_is_safe_path():
    base = os.getcwd()
    assert is_safe_path(base)
    assert not is_safe_path("/etc/passwd")
