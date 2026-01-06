import os
import tempfile
import pytest
from core.functions.load_tools_ui_config import load_tools_ui_config

def test_load_tools_ui_config_reads_valid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "ui_config.json")
        content = '{"ui": "config"}'
        with open(file_path, "w") as f:
            f.write(content)
        result = load_tools_ui_config(file_path)
        assert result["ui"] == "config"

def test_load_tools_ui_config_file_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "nope.json")
        assert load_tools_ui_config(file_path) is None

def test_load_tools_ui_config_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "bad.json")
        with open(file_path, "w") as f:
            f.write("notjson")
        assert load_tools_ui_config(file_path) is None