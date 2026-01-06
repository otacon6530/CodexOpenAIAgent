from core.functions.save_skill import save_skill
import os
import json

def test_save_skill(tmp_path, monkeypatch):
    import core.functions.save_skill as mod
    skills_dir = tmp_path / "skills"
    monkeypatch.setattr(mod, "SKILLS_DIR", str(skills_dir))
    # Normal case
    save_skill("foo", "desc", ["step"])
    file = skills_dir / "foo.json"
    assert file.exists()
    data = json.loads(file.read_text())
    assert data["name"] == "foo"

    # Invalid name (should still create file)
    save_skill("bar/baz", "desc", ["step"])
    file2 = skills_dir / "bar/baz.json"
    assert file2.exists()

    # Missing description/steps
    save_skill("empty", None, None)
    file3 = skills_dir / "empty.json"
    assert file3.exists()
    data3 = json.loads(file3.read_text())
    assert data3["description"] is None
    assert data3["steps"] is None

    # File write error (simulate by mocking open to raise IOError)
    import pytest
    from unittest.mock import patch
    with patch("builtins.open", side_effect=IOError("mocked error")):
        with pytest.raises(IOError):
            save_skill("fail", "desc", ["step"])
