import os

metadata = {
    'name': 'read_file',
    'description': 'Read file contents by line range.'
}


def run(args: str) -> str:
    if not args.strip():
        return 'read_file error: no arguments provided.'
    parts = [part.strip() for part in args.split('|')]
    path = parts[0]
    start = int(parts[1]) if len(parts) > 1 and parts[1] else None
    end = int(parts[2]) if len(parts) > 2 and parts[2] else None
    if not os.path.exists(path):
        return f'read_file error: {path} not found.'
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            lines = handle.readlines()
        start_idx = start - 1 if start else 0
        end_idx = end if end else len(lines)
        selected = ''.join(lines[start_idx:end_idx])
        return selected if selected else '(No content in specified range)'
    except Exception as exc:
        return f'read_file error: {exc}'
