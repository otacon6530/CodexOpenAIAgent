import pytest
import os
from core.functions.openai_client import OpenAIClient

class DummyResp:
    def __init__(self, lines, status=200):
        self._lines = lines
        self.status_code = status
        self.closed = False
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.closed = True
    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception("HTTP error")
    def iter_lines(self):
        for l in self._lines:
            yield l

def test_stream_chat_yields_and_last_response(monkeypatch):
    # Simulate two chunks and [DONE]
    import json
    chunks = [
        b"data: " + json.dumps({"choices":[{"delta":{"content":"Hello "}}]}).encode(),
        b"data: " + json.dumps({"choices":[{"delta":{"content":"world!"}}]}).encode(),
        b"data: [DONE]"
    ]
    def fake_post(*a, **k):
        return DummyResp(chunks)
    monkeypatch.setattr("requests.post", fake_post)
    client = OpenAIClient({"api_url": "http://x", "api_key": "k"})
    out = b""
    result = b""
    for delta in client.stream_chat([{"role": "user", "content": "hi"}]):
        result += delta.encode() if isinstance(delta, str) else delta
    assert b"Hello" in result and b"world" in result
    assert "Hello" in client.get_last_response() and "world" in client.get_last_response()

def test_stream_chat_skips_lines(monkeypatch):
    # Should skip lines not starting with b"data: "
    chunks = [b"notdata", b"data: [DONE]"]
    def fake_post(*a, **k):
        return DummyResp(chunks)
    monkeypatch.setattr("requests.post", fake_post)
    client = OpenAIClient({"api_url": "http://x", "api_key": "k"})
    list(client.stream_chat([{"role": "user", "content": "hi"}]))

def test_stream_chat_exception_in_yield(monkeypatch):
    # Should continue on exception in yield
    import json
    class BadResp(DummyResp):
        def iter_lines(self):
            yield b"data: " + json.dumps({"choices":[{"delta":{}}]}).encode()
            yield b"data: [DONE]"
    def fake_post(*a, **k):
        return BadResp([])
    monkeypatch.setattr("requests.post", fake_post)
    client = OpenAIClient({"api_url": "http://x", "api_key": "k"})
    list(client.stream_chat([{"role": "user", "content": "hi"}]))

def test_stream_chat_http_error(monkeypatch):
    def fake_post(*a, **k):
        return DummyResp([], status=500)
    monkeypatch.setattr("requests.post", fake_post)
    client = OpenAIClient({"api_url": "http://x", "api_key": "k"})
    with pytest.raises(Exception):
        list(client.stream_chat([{"role": "user", "content": "hi"}]))

def test_stream_chat_bad_json(monkeypatch):
    # Should skip bad json
    chunks = [b"data: notjson", b"data: [DONE]"]
    def fake_post(*a, **k):
        return DummyResp(chunks)
    monkeypatch.setattr("requests.post", fake_post)
    client = OpenAIClient({"api_url": "http://x", "api_key": "k"})
    list(client.stream_chat([{"role": "user", "content": "hi"}]))

def test_get_last_response():
    client = OpenAIClient({"api_url": "http://x", "api_key": "k"})
    client.last_response = "foo"
    assert client.get_last_response() == "foo"

def test_openai_client_init_default_model():
    # Should default to gpt-3.5-turbo
    c = OpenAIClient({"api_url": "x", "api_key": "y"})
    assert c.model == "gpt-3.5-turbo"

def test_openai_client_init_custom_model():
    c = OpenAIClient({"api_url": "x", "api_key": "y", "model": "foo"})
    assert c.model == "foo"

def test_stream_chat_empty_lines(monkeypatch):
    # Should handle no lines gracefully
    class DummyResp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def raise_for_status(self): pass
        def iter_lines(self): return iter([])
    monkeypatch.setattr("requests.post", lambda *a, **k: DummyResp())
    client = OpenAIClient({"api_url": "x", "api_key": "y"})
    assert list(client.stream_chat([{"role": "user", "content": "hi"}])) == []

def test_stream_chat_post_exception(monkeypatch):
    def fail_post(*a, **k):
        class Dummy:
            def __enter__(self): raise Exception("fail")
            def __exit__(self, *a): return False
        return Dummy()
    monkeypatch.setattr("requests.post", fail_post)
    client = OpenAIClient({"api_url": "x", "api_key": "y"})
    with pytest.raises(Exception):
        list(client.stream_chat([{"role": "user", "content": "hi"}]))
