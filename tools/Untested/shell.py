
import subprocess
import os
import platform

if os.name == 'nt':
    shell_desc = (
        'Run a shell command and return its output. Example: "dir" to list files, "type file.txt" to show a file.'
    )
else:
    shell_desc = (
        'Run a shell command and return its output. Example: "ls" to list files, "cat file.txt" to show a file.'
    )

metadata = {
    'name': 'shell',
    'description': shell_desc
}

def run(args):
    """
    Run a shell command and return its output or error.
    Usage: <tool:shell>your command here</tool>
    """
    if not args.strip():
        return 'No command provided.'
    try:
        result = subprocess.run(args, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return f'Error (code {result.returncode}): {error or output}'
        return output or '(No output)'
    except Exception as e:
        return f'Exception: {e}'
