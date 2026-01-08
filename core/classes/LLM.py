from core.functions.openai_client import OpenAIClient
from core.functions.llm_test_connection import test_connection  

class LLM:
    def __init__(self, config):
        self.client = OpenAIClient(config)
        self.test_connection = test_connection 
        self.test_connection(self)   

    def stream_chat(self, messages):
        return self.client.stream_chat(messages)

    def get_last_response(self):
        return self.client.get_last_response()
