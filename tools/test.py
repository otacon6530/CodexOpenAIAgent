import subprocess

metadata = {
    'name': 'test',
    'description': 'Run tests. Usage: <tool:test>test command</tool>'
}

def run(args):
    try:
        result = subprocess.run(args, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return f'Test failed: {error or output}'
        return output or 'All tests passed.'
    except Exception as e:
        return f'Test tool error: {e}'
