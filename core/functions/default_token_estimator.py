from typing import Optional

def default_token_estimator(text: Optional[str]) -> int:
    """Rough heuristic (characters / 4 + words) to estimate token usage."""
    if not text:
        return 0
    chars = len(text)
    words = len(text.split())
    return max(1, int(chars / 4) + words)
