from core.functions.make_entry_metadata import make_entry_metadata

def test_make_entry_metadata():
    meta = make_entry_metadata("hi", ["topic"], {"foo": 1}, 2, lambda x: 5)
    assert meta["tokens"] == 5
    assert meta["topics"] == ["topic"]
    assert meta["turn_id"] == 2
    assert meta["foo"] == 1
