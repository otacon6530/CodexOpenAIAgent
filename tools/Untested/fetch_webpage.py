import re

metadata = {
    'name': 'fetch_webpage',
    'description': 'Download and parse webpage content for summarization.'
}


def run(args: str) -> str:
    if not args.strip():
        return 'fetch_webpage error: no URL provided.'
    if '|' in args:
        url, query = args.split('|', 1)
        query = query.strip()
    else:
        url, query = args, ''
    url = url.strip()
    try:
        import requests  # type: ignore
    except ImportError:
        return 'fetch_webpage error: requests library not installed.'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        text = response.text
        if query:
            match = re.search(query, text, re.IGNORECASE)
            if match:
                start = max(match.start() - 120, 0)
                end = min(match.end() + 120, len(text))
                snippet = text[start:end]
                return f'Found query snippet:\n{snippet}'
            return 'Query not found in page.'
        return text[:2000] + ('\n...[truncated]...' if len(text) > 2000 else '')
    except Exception as exc:
        return f'fetch_webpage error: {exc}'
