import os
import json

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")

def save_skill(name, description, steps):
    payload = {"name": name, "description": description, "steps": steps}
    os.makedirs(SKILLS_DIR, exist_ok=True)
    with open(os.path.join(SKILLS_DIR, f"{name}.json"), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return True
