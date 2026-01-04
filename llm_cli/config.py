import os

def load_config():
    return {
        "api_url": os.environ.get("OPENAI_API_URL", "http://apple.stephensdev.com:11434/v1/chat/completions"),
        "api_key": os.environ.get("OPENAI_API_KEY", "sk-xxx"),
        "model": os.environ.get("OPENAI_MODEL", "qwen3:8b")
    }
