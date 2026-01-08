import pytest
from core.classes.LLM import API

class DummyClient:
    def stream_chat(self, messages):
        return ["response"]
    def get_last_response(self):
        return "last_response"

def test_api_stream_chat(monkeypatch):
    # Patch OpenAIClient to avoid real network and config dependency
    monkeypatch.setattr('core.classes.API.OpenAIClient', lambda config: DummyClient())
    api = API({"api_url": "x", "api_key": "y"})
    result = list(api.stream_chat([{"role": "user", "content": "hi"}]))
    assert result == ["response"]

def test_api_get_last_response(monkeypatch):
    monkeypatch.setattr('core.classes.API.OpenAIClient', lambda config: DummyClient())
    api = API({"api_url": "x", "api_key": "y"})
    assert api.get_last_response() == "last_response"
