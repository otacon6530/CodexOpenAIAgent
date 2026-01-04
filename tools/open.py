metadata = {
    'name': 'open',
    'description': 'Open files in your editor. Usage: <tool:open>filename</tool>'
}

def run(args):
    import os
    import subprocess
    filename = args.strip()
    if not filename:
        return 'No filename provided.'
    try:
        if os.name == 'nt':
            os.startfile(filename)
        elif os.name == 'posix':
            subprocess.run(['xdg-open', filename], check=True)
        else:
            return 'Unsupported OS.'
        return f'Opened {filename}.'
    except Exception as e:
        return f'Open tool error: {e}'
