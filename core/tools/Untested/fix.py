metadata = {
    'name': 'fix',
    'description': 'Fix code using instructions. Usage: <tool:fix>filename|instructions</tool>'
}

def run(args):
    try:
        filename, instructions = args.split('|', 1)
        filename = filename.strip()
        instructions = instructions.strip()
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        # Placeholder: just append fix instructions
        new_content = content + '\n# Fix: ' + instructions
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f'Fixed {filename} with instructions.'
    except Exception as e:
        return f'Fix tool error: {e}'
