import subprocess

metadata = {
    'name': 'revert',
    'description': 'Revert changes. Usage: <tool:revert>commit or file</tool>'
}

def run(args):
    try:
        result = subprocess.run(f'git checkout {args.strip()}', shell=True, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return f'Revert failed: {error or output}'
        return output or 'Revert successful.'
    except Exception as e:
        return f'Revert tool error: {e}'
