metadata = {
    'name': 'doc',
    'description': 'Generate or update documentation. Usage: <tool:doc>filename|instructions</tool>'
}

def run(args):
    try:
        filename, instructions = args.split('|', 1)
        filename = filename.strip()
        instructions = instructions.strip()
        with open(filename, 'a', encoding='utf-8') as f:
            f.write('\n# Doc: ' + instructions)
        return f'Documentation updated for {filename}.'
    except Exception as e:
        return f'Doc tool error: {e}'
