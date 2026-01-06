import os
import importlib.util

TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "tools")

def load_tools():
    tools = {}
    if not os.path.isdir(TOOLS_DIR):
        return tools
    for fname in os.listdir(TOOLS_DIR):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        path = os.path.join(TOOLS_DIR, fname)
        spec = importlib.util.spec_from_file_location(fname[:-3], path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "TOOLS"):
            for tool in mod.TOOLS:
                name = tool.get("name")
                run_fn = tool.get("run")
                desc = tool.get("description", "")
                if name and callable(run_fn):
                    tools[name] = {"run": run_fn, "description": desc}
        elif hasattr(mod, "metadata") and hasattr(mod, "run"):
            name = mod.metadata.get("name")
            if name and callable(mod.run):
                tools[name] = {
                    "run": mod.run,
                    "description": mod.metadata.get("description", ""),
                }
    return tools
