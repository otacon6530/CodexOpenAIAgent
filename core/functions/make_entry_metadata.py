from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, Optional

def make_entry_metadata(content: str, topics: Optional[Iterable[str]], metadata: Optional[Dict[str, Any]], turn_id: Optional[int], token_estimator: Callable[[str], int]) -> Dict[str, Any]:
    topics_list = list(topics) if topics else []
    tokens = token_estimator(content)
    entry_metadata = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tokens": tokens,
    }
    if topics_list:
        entry_metadata["topics"] = topics_list
    if metadata:
        entry_metadata.update(metadata)
    if turn_id is not None:
        entry_metadata["turn_id"] = turn_id
    return entry_metadata
