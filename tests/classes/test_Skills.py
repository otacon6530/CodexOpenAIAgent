from core.classes.Skills import Skills

def test_skills_list():
    s = Skills(list_func=lambda: ["a", "b"])
    assert s.list() == ["a", "b"]

def test_skills_load():
    s = Skills(load_func=lambda n: n.upper())
    assert s.load("foo") == "FOO"

def test_skills_save():
    s = Skills(save_func=lambda n, d, st: (n, d, st))
    assert s.save("n", "d", [1,2]) == ("n", "d", [1,2])
