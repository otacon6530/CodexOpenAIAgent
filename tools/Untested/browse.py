import os

metadata = {
    'name': 'browse',
    'description': 'Browse files and directories. Usage: <tool:browse>directory</tool>'
}

def run(args):
    directory = args.strip() or '.'
    try:
        files = os.listdir(directory)
        return '\n'.join(files)
    except Exception as e:
        return f'Browse tool error: {e}'
