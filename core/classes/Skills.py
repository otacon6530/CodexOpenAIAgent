from core.skills import list_skills, load_skill, save_skill

class Skills:
    def list(self):
        return list_skills()

    def load(self, name):
        return load_skill(name)

    def save(self, name, description, steps):
        return save_skill(name, description, steps)
