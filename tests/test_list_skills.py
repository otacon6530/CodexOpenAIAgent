from core.functions.list_skills import list_skills

def test_list_skills(tmp_path, monkeypatch):
    import core.functions.list_skills as mod
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_file = skills_dir / "foo.json"
    skill_file.write_text('{"name": "foo", "description": "bar", "steps": []}')
    monkeypatch.setattr(mod, "SKILLS_DIR", str(skills_dir))
    skills = list_skills()
    assert skills[0]["name"] == "foo"

def test_list_skills_empty(monkeypatch, tmp_path):
    import core.functions.list_skills as mod
    monkeypatch.setattr(mod, "SKILLS_DIR", str(tmp_path / "nope"))
    assert mod.list_skills() == []

def test_list_skills_nonjson(monkeypatch, tmp_path):
    import core.functions.list_skills as mod
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "foo.txt").write_text("not json")
    monkeypatch.setattr(mod, "SKILLS_DIR", str(skills_dir))
    assert mod.list_skills() == []

def test_list_skills_json_error(monkeypatch, tmp_path):
    import core.functions.list_skills as mod
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "foo.json").write_text("not json")
    monkeypatch.setattr(mod, "SKILLS_DIR", str(skills_dir))
    assert mod.list_skills() == []
