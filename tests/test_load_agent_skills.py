import os
import tempfile
import pytest
from core.functions.load_agent_skills import load_agent_skills

def test_load_agent_skills_reads_valid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "skills.json")
        content = '[{"name": "skill1"}, {"name": "skill2"}]'
        with open(file_path, "w") as f:
            f.write(content)
        result = load_agent_skills(file_path)
        assert isinstance(result, list)
        assert result[0]["name"] == "skill1"

def test_load_agent_skills_file_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "nope.json")
        assert load_agent_skills(file_path) is None

def test_load_agent_skills_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "bad.json")
        with open(file_path, "w") as f:
            f.write("notjson")
        assert load_agent_skills(file_path) is None