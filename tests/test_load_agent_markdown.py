import os
import pytest
from core.functions.load_agent_markdown import load_agent_markdown

def test_load_agent_markdown_invalid_path():
    # None, not a string, or path does not exist
    assert load_agent_markdown(None) is None
    assert load_agent_markdown(123) is None
    assert load_agent_markdown("/unlikely/to/exist/agent.md") is None

def test_load_agent_markdown_open_exception(monkeypatch, tmp_path):
    # File exists but open fails
    file_path = tmp_path / "agent.md"
    file_path.write_text("test")
    def bad_open(*a, **k):
        raise OSError("fail")
    monkeypatch.setattr("builtins.open", bad_open)

    assert load_agent_markdown(str(file_path)) is None
from core.functions.load_agent_markdown import load_agent_markdown



