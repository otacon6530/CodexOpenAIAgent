from datetime import datetime, timezone
from typing import Any, Callable, Dict, List
from .shorten import shorten

def append_long_term_entry(messages: List[Dict[str, Any]], long_term_context: List[Dict[str, Any]], max_long_term_entries: int, token_estimator: Callable[[str], int], refresh_running_summary: Callable[[], None]):
    if not messages:
        return
    topics = set()
    user_snippets: List[str] = []
    assistant_snippets: List[str] = []
    other_snippets: List[str] = []
    turn_ids = set()
    for msg in messages:
        metadata = msg.get("metadata", {})
        turn_val = metadata.get("turn_id")
        if isinstance(turn_val, int):
            turn_ids.add(turn_val)
        for topic in metadata.get("topics", []) or []:
            topics.add(topic)
        snippet = shorten(msg.get("content", ""))
        role = msg.get("role")
        if role == "user":
            user_snippets.append(snippet)
        elif role == "assistant":
            assistant_snippets.append(snippet)
        else:
            other_snippets.append(f"{role}: {snippet}")
    segments: List[str] = []
    if user_snippets:
        segments.append("User: " + " | ".join(user_snippets))
    if assistant_snippets:
        segments.append("Assistant: " + " | ".join(assistant_snippets))
    if other_snippets:
        segments.extend(other_snippets)
    entry = {
        "summary": "; ".join(segments),
        "turn_ids": sorted(turn_ids),
        "topics": sorted(topics),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    long_term_context.append(entry)
    if len(long_term_context) > max_long_term_entries:
        long_term_context[:] = long_term_context[-max_long_term_entries:]
    refresh_running_summary()
