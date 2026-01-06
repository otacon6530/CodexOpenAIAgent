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
