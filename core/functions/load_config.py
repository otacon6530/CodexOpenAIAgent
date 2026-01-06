import os
from core.functions.parse_bool import parse_bool

def load_config():
    return {
        "api_url": os.environ.get("OPENAI_API_URL", "http://apple.stephensdev.com:11434/v1/chat/completions"),
        "api_key": os.environ.get("OPENAI_API_KEY", "sk-xxx"),
        "model": os.environ.get("OPENAI_MODEL", "qwen3:8b"),
        "chain_limit": int(os.environ.get("LLM_CHAIN_LIMIT", os.environ.get("CHAIN_LIMIT", 25))),
        "debug_metrics": parse_bool(os.environ.get("LLM_DEBUG_METRICS"), default=True),
    }
