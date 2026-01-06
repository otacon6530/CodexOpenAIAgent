from core.functions.is_safe_path import is_safe_path

class Sandbox:
    def __init__(self, base_dir=None, safe_path_func=None):
        self.base_dir = base_dir
        self._safe_path_func = safe_path_func or is_safe_path

    def is_safe_path(self, path):
        return self._safe_path_func(path)
