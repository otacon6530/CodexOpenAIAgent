from core.functions.shorten import shorten

def test_shorten():
    assert shorten("hello") == "hello"
    assert shorten("a"*200, 10).endswith("...")
    # Normal string, no truncation
    # Truncation
    # Empty string
    assert shorten("") == ""
    # Limit = 0
    assert shorten("abc", 0) == "..."
    # Limit equal to string length
    assert shorten("abc", 3) == "abc"
    # Non-string input should raise
    import pytest
    with pytest.raises(TypeError):
        shorten(12345, 3)
