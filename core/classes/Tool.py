from core.functions._load_all_tools import _load_all_tools

class Tool:
    def __init__(self):
        self.load_tools = _load_all_tools
        self.tools = self.load_tools()
