import os
import json

SKILLS_DIR = os.path.join(os.path.dirname(__file__), '..', 'skills')

# Each skill is a JSON file: {"name": ..., "description": ..., "steps": [ ... ]}

def list_skills():
    skills = []
    if not os.path.exists(SKILLS_DIR):
        return skills
    for fname in os.listdir(SKILLS_DIR):
        if fname.endswith('.json'):
            with open(os.path.join(SKILLS_DIR, fname), 'r', encoding='utf-8') as f:
                try:
                    skill = json.load(f)
                    skills.append(skill)
                except Exception:
                    continue
    return skills

def save_skill(name, description, steps):
    skill = {"name": name, "description": description, "steps": steps}
    with open(os.path.join(SKILLS_DIR, f"{name}.json"), 'w', encoding='utf-8') as f:
        json.dump(skill, f, indent=2)
    return True

def load_skill(name):
    path = os.path.join(SKILLS_DIR, f"{name}.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
