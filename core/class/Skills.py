from core.functions.list_skills import list_skills
from core.functions.load_skill import load_skill
from core.functions.save_skill import save_skill

class Skills:
    def list(self):
        return list_skills()

    def load(self, name):
        return load_skill(name)

    def save(self, name, description, steps):
        return save_skill(name, description, steps)
