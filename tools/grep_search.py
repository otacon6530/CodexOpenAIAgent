import os
import re

metadata = {
    'name': 'grep_search',
    'description': 'Regex or plain-text search across files.'
}


def run(args: str) -> str:
    if '|' not in args:
        return 'grep_search usage: pattern|filename.'
    pattern, filename = args.split('|', 1)
    pattern = pattern.strip()
    filename = filename.strip()
    if not pattern or not filename:
        return 'grep_search error: pattern and filename required.'
    if not os.path.exists(filename):
        return f'grep_search error: {filename} not found.'
    try:
        with open(filename, 'r', encoding='utf-8') as handle:
            content = handle.read()
        matches = re.findall(pattern, content, flags=re.MULTILINE)
        if not matches:
            return 'No matches found.'
        sample = matches[:5]
        return f'Found {len(matches)} matches: {sample}'
    except Exception as exc:
        return f'grep_search error: {exc}'
