import os
def load_agent_markdown(path):
    if not path or not isinstance(path, (str, bytes, os.PathLike)) or not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None
