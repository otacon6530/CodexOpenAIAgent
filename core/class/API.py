from core.api import OpenAIClient

class API:
    def __init__(self, config):
        self.client = OpenAIClient(config)

    def stream_chat(self, messages):
        return self.client.stream_chat(messages)

    def get_last_response(self):
        return self.client.get_last_response()
