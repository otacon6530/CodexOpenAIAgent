import os
import json

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")

def load_skill(name):
    path = os.path.join(SKILLS_DIR, f"{name}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)
