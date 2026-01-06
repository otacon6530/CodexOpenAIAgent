import os
import pytest
from core.functions.load_skill_markdown import load_skill_markdown

def test_load_skill_markdown_not_exists():
    assert load_skill_markdown("/unlikely/to/exist/skill.md") is None

def test_load_skill_markdown_open_exception(monkeypatch, tmp_path):
    file_path = tmp_path / "skill.md"
    file_path.write_text("test")
    def bad_open(*a, **k):
        raise Exception("fail")
    monkeypatch.setattr("builtins.open", bad_open)
    assert load_skill_markdown(str(file_path)) is None

def test_load_skill_markdown_open_exception(monkeypatch, tmp_path):
    file_path = tmp_path / "skill.md"
    file_path.write_text("test")
    def bad_open(*a, **k):
        raise OSError("fail")
    monkeypatch.setattr("builtins.open", bad_open)
    assert load_skill_markdown(str(file_path)) is None