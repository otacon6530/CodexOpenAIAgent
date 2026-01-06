
import copy
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

def default_token_estimator(text: str) -> int:
	"""Rough heuristic (characters / 4 + words) to estimate token usage."""
	if not text or not text.strip():
		return 0
	chars = len(text)
	words = len(text.split())
	return max(1, int(chars / 4) + words)

def shorten(text: str, limit: int = 120) -> str:
	stripped = text.strip()
	if len(stripped) <= limit:
		return stripped
	return stripped[: limit - 3].rstrip() + "..."

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

def promote_to_long_term(message: Dict[str, Any], evicted_turn_buffer: Dict[int, List[Dict[str, Any]]], is_turn_in_window: Callable[[int], bool], append_long_term_entry: Callable[[List[Dict[str, Any]]], None]):
	metadata = message.get("metadata", {})
	turn_id = metadata.get("turn_id")
	if turn_id is None:
		append_long_term_entry([message])
		return
	evicted_turn_buffer[turn_id].append(message)
	if not is_turn_in_window(turn_id):
		buffered = evicted_turn_buffer.pop(turn_id, [])
		if buffered:
			append_long_term_entry(buffered)

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
