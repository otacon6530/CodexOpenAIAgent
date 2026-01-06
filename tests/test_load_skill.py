from core.functions.load_skill import load_skill
import os
import json

def test_load_skill(tmp_path, monkeypatch):
    import core.functions.load_skill as mod
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_file = skills_dir / "foo.json"
    skill_file.write_text(json.dumps({"name": "foo", "description": "bar", "steps": []}))
    monkeypatch.setattr(mod, "SKILLS_DIR", str(skills_dir))
    result = load_skill("foo")
    assert result["name"] == "foo"
