import os
import tempfile
import pytest
from core.functions.load_skill_tools import load_skill_tools

def test_load_skill_tools_reads_valid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "tools.json")
        content = '[{"name": "tool1"}, {"name": "tool2"}]'
        with open(file_path, "w") as f:
            f.write(content)
        result = load_skill_tools(file_path)
        assert isinstance(result, list)
        assert result[0]["name"] == "tool1"

def test_load_skill_tools_file_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "nope.json")
        assert load_skill_tools(file_path) is None

def test_load_skill_tools_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "bad.json")
        with open(file_path, "w") as f:
            f.write("notjson")
        assert load_skill_tools(file_path) is None