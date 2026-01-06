from core.functions.load_agent_markdown import load_agent_markdown

def test_load_agent_markdown(tmp_path, monkeypatch):
    md = tmp_path / "agent.md"
    md.write_text("hello agent")
    monkeypatch.chdir(tmp_path)
    result = load_agent_markdown()
    assert "hello agent" in result
