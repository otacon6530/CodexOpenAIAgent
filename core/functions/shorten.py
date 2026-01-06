def shorten(text: str, limit: int = 120) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 3].rstrip() + "..."
