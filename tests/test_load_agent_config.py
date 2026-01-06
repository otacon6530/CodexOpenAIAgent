import os
import tempfile
import pytest
from core.functions.load_agent_config import load_agent_config

def test_load_agent_config_reads_valid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "agent.json")
        content = '{"name": "agent", "desc": "test"}'
        with open(file_path, "w") as f:
            f.write(content)
        result = load_agent_config(file_path)
        assert result["name"] == "agent"

def test_load_agent_config_file_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "nope.json")
        assert load_agent_config(file_path) is None

def test_load_agent_config_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "bad.json")
        with open(file_path, "w") as f:
            f.write("notjson")
        assert load_agent_config(file_path) is None