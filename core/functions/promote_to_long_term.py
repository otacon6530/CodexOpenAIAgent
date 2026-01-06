from typing import Any, Callable, Dict, List

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
