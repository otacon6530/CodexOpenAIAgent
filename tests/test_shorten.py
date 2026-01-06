from core.functions.shorten import shorten

def test_shorten():
    assert shorten("hello") == "hello"
    assert shorten("a"*200, 10).endswith("...")
