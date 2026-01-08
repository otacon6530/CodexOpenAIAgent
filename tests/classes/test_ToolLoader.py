from core.classes.Tool import ToolLoader

def test_tool_loader_load(monkeypatch):
    monkeypatch.setattr('core.classes.ToolLoader.load_tools', lambda: [1,2,3])
    tl = ToolLoader()
    assert tl.load() == [1,2,3]
