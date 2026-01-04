import os

metadata = {
    'name': 'create_file',
    'description': 'Create a new file with given content.'
}


def run(args: str) -> str:
    if not args.strip():
        return 'create_file error: no arguments provided.'
    if '|' in args:
        path, content = args.split('|', 1)
    else:
        path, content = args, ''
    path = path.strip()
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(content)
        return f'Created file {path}.'
    except Exception as exc:
        return f'create_file error: {exc}'