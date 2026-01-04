import os
import importlib.util

TOOLS_DIR = os.path.join(os.path.dirname(__file__), '..', 'tools')

def load_tools():
    tools = {}
    for fname in os.listdir(TOOLS_DIR):
        if fname.endswith('.py') and not fname.startswith('_'):
            path = os.path.join(TOOLS_DIR, fname)
            spec = importlib.util.spec_from_file_location(fname[:-3], path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, 'run') and hasattr(mod, 'metadata'):
                tools[mod.metadata['name']] = {
                    'run': mod.run,
                    'description': mod.metadata.get('description', '')
                }
    return tools
