import os

metadata = {
    'name': 'list_dir',
    'description': 'Directory listing (files and subfolders).'
}


def run(args: str) -> str:
    path = args.strip() or '.'
    if not os.path.exists(path):
        return f'list_dir error: {path} not found.'
    try:
        entries = sorted(os.listdir(path))
        return '\n'.join(entries)
    except Exception as exc:
        return f'list_dir error: {exc}'
