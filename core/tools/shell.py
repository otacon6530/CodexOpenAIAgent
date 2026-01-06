
import subprocess
import os
import platform

os_type = platform.system()
if os_type == 'Windows':
    shell_desc = (
        'Run a shell command and return its output. OS: Windows. Example: "dir" to list files, "type file.txt" to show a file.'
    )
elif os_type == 'Darwin':
    shell_desc = (
        'Run a shell command and return its output. OS: macOS. Example: "ls" to list files, "cat file.txt" to show a file.'
    )   
else:
    shell_desc = (
        'Run a shell command and return its output. OS: Linux. Example: "ls" to list files, "cat file.txt" to show a file.'
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

# For tool auto-discovery
TOOLS = [
    {
        'name': metadata['name'],
        'description': metadata['description'],
        'run': run,
    }
]
