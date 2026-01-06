from core.config import load_config

class Config:
    def __init__(self):
        self.config = load_config()

    def __getitem__(self, key):
        return self.config[key]

    def get(self, key, default=None):
        return self.config.get(key, default)

    def as_dict(self):
        return dict(self.config)
