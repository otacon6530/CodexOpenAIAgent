import glob
import os
from typing import Iterable, Optional

def load_agent_markdown(search_dirs: Optional[Iterable[str]] = None) -> Optional[str]:
    if search_dirs is None:
        cwd = os.getcwd()
        search_dirs = [cwd, os.path.join(cwd, "cli")]
    for directory in search_dirs:
        try:
            for path in glob.glob(os.path.join(directory, "*.[mM][dD]")):
                if os.path.basename(path).lower() == "agent.md":
                    with open(path, "r", encoding="utf-8") as handle:
                        return handle.read()
        except Exception:
            continue
    return None
