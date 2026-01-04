import subprocess

metadata = {
    'name': 'get_changed_files',
    'description': 'List git changes (staged/unstaged/conflicts).'
}


def run(_args: str) -> str:
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=10)
        output = result.stdout.strip()
        return output or 'No changes.'
    except Exception as exc:
        return f'get_changed_files error: {exc}'
