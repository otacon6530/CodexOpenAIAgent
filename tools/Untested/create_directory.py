import os

metadata = {
    'name': 'create_directory',
    'description': 'Recursively create folders (mkdir -p).'
}


def run(args: str) -> str:
    path = args.strip()
    if not path:
        return 'create_directory error: no path provided.'
    try:
        os.makedirs(path, exist_ok=True)
        return f'Created directory {path}.'
    except Exception as exc:
        return f'create_directory error: {exc}'
