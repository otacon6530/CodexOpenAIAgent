metadata = {
    'name': 'refactor',
    'description': 'Refactor code. Usage: <tool:refactor>filename|instructions</tool>'
}

def run(args):
    try:
        filename, instructions = args.split('|', 1)
        filename = filename.strip()
        instructions = instructions.strip()
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        # Placeholder: just append refactor instructions
        new_content = content + '\n# Refactor: ' + instructions
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f'Refactored {filename} with instructions.'
    except Exception as e:
        return f'Refactor tool error: {e}'
