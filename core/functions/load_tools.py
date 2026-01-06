import os
import importlib.util
from core.classes.Logger import Logger

TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "tools")
logger = Logger()

def load_tools():
    logger.info("load_tools() called")
    tools = {}
    logger.info(f"Checking if tools directory exists: {TOOLS_DIR}")
    if not os.path.isdir(TOOLS_DIR):
        logger.warning(f"Tools directory does not exist: {TOOLS_DIR}")
        return tools
    logger.info(f"Listing files in tools directory: {TOOLS_DIR}")
    for fname in os.listdir(TOOLS_DIR):
        logger.info(f"Found file: {fname}")
        if not fname.endswith(".py") or fname.startswith("_"):
            logger.info(f"Skipping file (not a tool): {fname}")
            continue
        path = os.path.join(TOOLS_DIR, fname)
        logger.info(f"Loading module from: {path}")
        try:
            spec = importlib.util.spec_from_file_location(fname[:-3], path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:
            logger.error(f"Failed to load module {fname}: {e}")
            continue
        if hasattr(mod, "TOOLS"):
            logger.info(f"Module {fname} has TOOLS attribute")
            tools_attr = mod.TOOLS
            if not isinstance(tools_attr, list):
                logger.warning(f"TOOLS attribute in {fname} is not a list")
                continue
            for tool in tools_attr:
                name = tool.get("name")
                run_fn = tool.get("run")
                desc = tool.get("description", "")
                logger.info(f"Processing tool in TOOLS: {name}")
                if name and callable(run_fn):
                    tools[name] = {"run": run_fn, "description": desc}
                    logger.info(f"Loaded tool: {name}")
                else:
                    logger.warning(f"Invalid tool definition in {fname}: {tool}")
        elif hasattr(mod, "metadata") and hasattr(mod, "run"):
            logger.info(f"Module {fname} has metadata and run attributes")
            name = mod.metadata.get("name")
            if name and callable(mod.run):
                tools[name] = {
                    "run": mod.run,
                    "description": mod.metadata.get("description", ""),
                }
                logger.info(f"Loaded tool: {name}")
            else:
                logger.warning(f"Invalid metadata/run in {fname}")
        else:
            logger.info(f"Module {fname} does not have TOOLS or metadata/run")
    logger.info(f"Finished loading tools. Total loaded: {len(tools)}")
    return tools
