import os
import json

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")

def list_skills():
    skills = []
    if not os.path.exists(SKILLS_DIR):
        return skills
    for fname in os.listdir(SKILLS_DIR):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(SKILLS_DIR, fname), "r", encoding="utf-8") as handle:
            try:
                skills.append(json.load(handle))
            except Exception:
                continue
    return skills

def save_skill(name, description, steps):
    payload = {"name": name, "description": description, "steps": steps}
    os.makedirs(SKILLS_DIR, exist_ok=True)
    with open(os.path.join(SKILLS_DIR, f"{name}.json"), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return True

def load_skill(name):
    path = os.path.join(SKILLS_DIR, f"{name}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)
