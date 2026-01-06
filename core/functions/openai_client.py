import requests

class OpenAIClient:
    def __init__(self, config):
        self.api_url = config["api_url"]
        self.api_key = config["api_key"]
        self.model = config.get("model", "gpt-3.5-turbo")
        self.last_response = ""

    def stream_chat(self, messages):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        with requests.post(self.api_url, headers=headers, json=data, stream=True) as resp:
            resp.raise_for_status()
            content = ""
            for line in resp.iter_lines():
                if not line or not line.startswith(b"data: "):
                    continue
                payload = line[6:]
                if payload == b"[DONE]":
                    break
                try:
                    import json
                    chunk = json.loads(payload)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        content += delta
                        yield delta
                except Exception:
                    continue
            self.last_response = content

    def get_last_response(self):
        return self.last_response
