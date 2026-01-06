import subprocess

metadata = {
    'name': 'run',
    'description': 'Run shell commands. Usage: <tool:run>your command here</tool>'
}

def run(args):
    try:
        result = subprocess.run(args, shell=True, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return f'Error (code {result.returncode}): {error or output}'
        return output or '(No output)'
    except Exception as e:
        return f'Run tool error: {e}'
