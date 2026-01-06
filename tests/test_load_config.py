from core.functions.load_config import load_config

def test_load_config(monkeypatch):
    monkeypatch.setenv("OPENAI_API_URL", "http://test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    config = load_config()
    assert config["api_url"] == "http://test"
    assert config["api_key"] == "sk-test"
