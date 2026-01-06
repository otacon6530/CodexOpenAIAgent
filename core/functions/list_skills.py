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
