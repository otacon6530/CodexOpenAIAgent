import os

BASE_DIR = os.path.abspath(os.getcwd())

def is_safe_path(path):
    abs_path = os.path.abspath(path)
    return abs_path.startswith(BASE_DIR)
