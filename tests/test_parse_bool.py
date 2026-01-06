from core.functions.parse_bool import parse_bool

def test_parse_bool():
    assert parse_bool("true")
    assert not parse_bool("false")
    assert parse_bool("1")
    assert not parse_bool(None)
