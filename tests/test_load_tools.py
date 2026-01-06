from core.functions.load_tools import load_tools

import os
import types
import sys
from core.functions import load_tools

def test_load_tools_empty(monkeypatch, tmp_path):
    import core.functions.load_tools as mod
    monkeypatch.setattr(mod, "TOOLS_DIR", str(tmp_path / "nope"))
    assert mod.load_tools() == {}

def test_load_tools_py_and_metadata(monkeypatch, tmp_path):
    import core.functions.load_tools as mod
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    # Tool with TOOLS attribute
    tool_py = tools_dir / "foo.py"
    tool_py.write_text("TOOLS = [{ 'name': 'foo', 'run': lambda x: x, 'description': 'desc'}]")
    # Tool with metadata/run
    tool2_py = tools_dir / "bar.py"
    tool2_py.write_text("metadata = {'name': 'bar', 'description': 'desc'}\ndef run(): pass")
    monkeypatch.setattr(mod, "TOOLS_DIR", str(tools_dir))
    result = mod.load_tools()
    assert "foo" in result and "bar" in result

def test_load_tools_skips(monkeypatch, tmp_path):
    import core.functions.load_tools as mod
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    (tools_dir / "_ignore.py").write_text("")
    (tools_dir / "notpy.txt").write_text("")
    monkeypatch.setattr(mod, "TOOLS_DIR", str(tools_dir))
    assert mod.load_tools() == {}
