metadata = {
    'name': 'edit',
    'description': 'Edit files using instructions. Usage: <tool:edit>filename|instructions</tool>'
}

def run(args):
    try:
        filename, instructions = args.split('|', 1)
        filename = filename.strip()
        instructions = instructions.strip()
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        # Placeholder: just append instructions to the file for now
        new_content = content + '\n# Edit: ' + instructions
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f'Edited {filename} with instructions.'
    except Exception as e:
        return f'Edit tool error: {e}'
