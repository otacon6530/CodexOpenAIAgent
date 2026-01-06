import os
import tempfile
import pytest
from core.functions.load_agent_system_prompt import load_agent_system_prompt

def test_load_agent_system_prompt_reads_valid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "system_prompt.json")
        content = '{"prompt": "hello"}'
        with open(file_path, "w") as f:
            f.write(content)
        result = load_agent_system_prompt(file_path)
        assert result["prompt"] == "hello"

def test_load_agent_system_prompt_file_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "nope.json")
        assert load_agent_system_prompt(file_path) is None

def test_load_agent_system_prompt_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "bad.json")
        with open(file_path, "w") as f:
            f.write("notjson")
        assert load_agent_system_prompt(file_path) is None