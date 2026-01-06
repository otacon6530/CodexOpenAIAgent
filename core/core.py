import json
import re
import sys
import time

from core.api import OpenAIClient
from core.functions.load_config import load_config
from core.classes.History import History
from core.functions.discover_mcp_tools import discover_mcp_tools
from core.functions.run_mcp_tool import run_mcp_tool
from core.functions.list_skills import list_skills
from core.functions.load_skill import load_skill
from core.functions.save_skill import save_skill
from core.functions.seed_history_with_system_prompts import seed_history_with_system_prompts
from core.functions.load_tools import load_tools

TOOL_PATTERN = re.compile(r"<tool:([a-zA-Z0-9_.\-]+)>(.*?)</tool>", re.DOTALL)
_PENDING_MESSAGES = []


def _load_all_tools():
	tools = load_tools()
	mcp_tools = discover_mcp_tools()
	for name, description in mcp_tools.items():
		tools[name] = {
			"run": lambda arguments, n=name: run_mcp_tool(n, arguments),
			"description": f"(MCP) {description}",
		}
	return tools

...existing code from chat_process.py...
