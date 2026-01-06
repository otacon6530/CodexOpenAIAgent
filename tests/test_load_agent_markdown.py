import os
import tempfile
import pytest
from core.functions.load_agent_markdown import load_agent_markdown

def test_load_agent_markdown_reads_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "agent.md")
        content = "# Agent\nHello"
        with open(file_path, "w") as f:
            f.write(content)
        result = load_agent_markdown(file_path)
        assert result == content

def test_load_agent_markdown_file_not_found():
    # Should return None if file does not exist
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "nope.md")
        assert load_agent_markdown(file_path) is None


