from core.functions.load_tools import load_tools

def test_load_tools(monkeypatch):
    # Just check it returns a dict, actual dynamic loading is integration
    tools = load_tools()
    assert isinstance(tools, dict)
