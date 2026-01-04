import glob

metadata = {
    'name': 'file_search',
    'description': 'Glob search for filenames within workspace.'
}


def run(args: str) -> str:
    pattern = args.strip()
    if not pattern:
        return 'file_search error: no pattern provided.'
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        return 'No files matched the pattern.'
    matches.sort()
    return '\n'.join(matches[:200])
