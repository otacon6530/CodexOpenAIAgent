import os
import json

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")

def save_skill(name, description, steps):
    payload = {"name": name, "description": description, "steps": steps}
    os.makedirs(SKILLS_DIR, exist_ok=True)
    file_path = os.path.join(SKILLS_DIR, f"{name}.json")
    parent_dir = os.path.dirname(file_path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return True
