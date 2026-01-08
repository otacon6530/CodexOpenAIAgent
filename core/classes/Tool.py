from core.functions._load_all_tools import _load_all_tools
from core.functions.core_utils import parse_editor_payload
from core.functions.editor_tools import inject_editor_tools
from core.functions._request_editor_query import _request_editor_query 

class Tool:
    def __init__(self):
        self.load_tools = _load_all_tools
        self.tools = self.load_tools()
        inject_editor_tools(self.tools, _request_editor_query, parse_editor_payload)
