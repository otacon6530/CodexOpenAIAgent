from core.sandbox import is_safe_path

class Sandbox:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir

    def is_safe_path(self, path):
        return is_safe_path(path)
