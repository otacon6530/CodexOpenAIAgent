import types
import sys
import tempfile
import importlib.util
import pytest
from core.functions import load_tools

def test_load_tools_tools_not_list(monkeypatch, tmp_path):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    tool_py = tools_dir / "foo.py"
    tool_py.write_text("TOOLS = 123")
    monkeypatch.setattr(load_tools, "TOOLS_DIR", str(tools_dir))
    # Should not raise, should skip
    assert load_tools.load_tools() == {}

def test_load_tools_run_not_callable(monkeypatch, tmp_path):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    tool_py = tools_dir / "foo.py"
    tool_py.write_text("TOOLS = [{ 'name': 'foo', 'run': 123, 'description': 'desc'}]")
    monkeypatch.setattr(load_tools, "TOOLS_DIR", str(tools_dir))
    assert load_tools.load_tools() == {}

def test_load_tools_metadata_missing_name(monkeypatch, tmp_path):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    tool_py = tools_dir / "foo.py"
    tool_py.write_text("metadata = {'description': 'desc'}\ndef run(): pass")
    monkeypatch.setattr(load_tools, "TOOLS_DIR", str(tools_dir))
    assert load_tools.load_tools() == {}

def test_load_tools_metadata_run_not_callable(monkeypatch, tmp_path):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    tool_py = tools_dir / "foo.py"
    tool_py.write_text("metadata = {'name': 'foo', 'description': 'desc'}\nrun = 123")
    monkeypatch.setattr(load_tools, "TOOLS_DIR", str(tools_dir))
    assert load_tools.load_tools() == {}