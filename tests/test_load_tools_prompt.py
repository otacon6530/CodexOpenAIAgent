import os
import tempfile
import pytest
from core.functions.load_tools_prompt import load_tools_prompt

def test_load_tools_prompt_reads_valid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "tools_prompt.json")
        content = '{"prompt": "tools!"}'
        with open(file_path, "w") as f:
            f.write(content)
        result = load_tools_prompt(file_path)
        assert result["prompt"] == "tools!"

def test_load_tools_prompt_file_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "nope.json")
        assert load_tools_prompt(file_path) is None

def test_load_tools_prompt_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "bad.json")
        with open(file_path, "w") as f:
            f.write("notjson")
        assert load_tools_prompt(file_path) is None