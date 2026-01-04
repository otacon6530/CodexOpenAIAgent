import subprocess

metadata = {
    'name': 'commit',
    'description': 'Create git commits with messages. Usage: <tool:commit>commit message</tool>'
}

def run(args):
    try:
        result = subprocess.run(f'git commit -am "{args.strip()}"', shell=True, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return f'Commit failed: {error or output}'
        return output or 'Commit successful.'
    except Exception as e:
        return f'Commit tool error: {e}'
