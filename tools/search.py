import re

metadata = {
    'name': 'search',
    'description': 'Search for text in files. Usage: <tool:search>pattern|filename</tool>'
}

def run(args):
    try:
        pattern, filename = args.split('|', 1)
        pattern = pattern.strip()
        filename = filename.strip()
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        matches = re.findall(pattern, content)
        return f'Found {len(matches)} matches: {matches[:5]}'
    except Exception as e:
        return f'Search tool error: {e}'
