from core.functions.save_skill import save_skill
import os
import json

def test_save_skill(tmp_path, monkeypatch):
    import core.functions.save_skill as mod
    skills_dir = tmp_path / "skills"
    monkeypatch.setattr(mod, "SKILLS_DIR", str(skills_dir))
    save_skill("foo", "desc", ["step"])
    file = skills_dir / "foo.json"
    assert file.exists()
    data = json.loads(file.read_text())
    assert data["name"] == "foo"
