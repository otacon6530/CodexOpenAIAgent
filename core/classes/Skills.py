from core.functions.list_skills import list_skills
from core.functions.load_skill import load_skill
from core.functions.save_skill import save_skill

class Skills:
    def __init__(self, list_func=None, load_func=None, save_func=None):
        self._list_func = list_func or list_skills
        self._load_func = load_func or load_skill
        self._save_func = save_func or save_skill

    def list(self):
        return self._list_func()

    def load(self, name):
        return self._load_func(name)

    def save(self, name, description, steps):
        return self._save_func(name, description, steps)
