import subprocess

metadata = {
    'name': 'run_in_terminal',
    'description': 'Execute PowerShell commands in persistent terminal.'
}


def run(args: str) -> str:
    command = args.strip()
    if not command:
        return 'run_in_terminal error: no command provided.'
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return f'Command failed (code {result.returncode}): {error or output}'
        return output or '(No output)'
    except Exception as exc:
        return f'run_in_terminal error: {exc}'
