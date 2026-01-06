from __future__ import annotations

import copy
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional


def _default_token_estimator(text: str) -> int:
    """Rough heuristic (characters / 4 + words) to estimate token usage."""
    if not text:
        return 0
    chars = len(text)
    words = len(text.split())
    return max(1, int(chars / 4) + words)


class ConversationHistory:
    """Tracks short-term messages with a token-aware window and long-term summaries."""

    def __init__(
        self,
        token_window: int = 1200,
        summary_token_budget: int = 400,
        token_estimator: Optional[Callable[[str], int]] = None,
        max_long_term_entries: int = 50,
    ) -> None:
        self.token_window = token_window
        self.summary_token_budget = summary_token_budget
        self.max_long_term_entries = max_long_term_entries
        self._estimate_tokens = token_estimator or _default_token_estimator

        self._messages: List[Dict[str, Any]] = []
        self._window_tokens = 0
        self._turn_id = 0
        self._active_turn_id = 0

        self.long_term_context: List[Dict[str, Any]] = []
        self.running_summary: str = ""

        self._evicted_turn_buffer: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_system_message(self, content: str, *, topics: Optional[Iterable[str]] = None) -> None:
        self._append_message("system", content, topics=topics, turn_id=None)

    def add_user_message(self, content: str, *, topics: Optional[Iterable[str]] = None) -> None:
        self._turn_id += 1
        self._active_turn_id = self._turn_id
        self._append_message("user", content, topics=topics, turn_id=self._active_turn_id)

    def add_assistant_message(self, content: str, *, topics: Optional[Iterable[str]] = None) -> None:
        turn_id = self._active_turn_id or self._turn_id
        self._append_message("assistant", content, topics=topics, turn_id=turn_id)
        self._refresh_running_summary()

    def add_message(
        self,
        role: str,
        content: str,
        *,
        topics: Optional[Iterable[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        turn_id: Optional[int] = None,
    ) -> None:
        if role == "user":
            self.add_user_message(content, topics=topics)
            return
        if role == "assistant":
            self.add_assistant_message(content, topics=topics)
            return
        self._append_message(role, content, topics=topics, metadata=metadata, turn_id=turn_id)

    def get_messages(
        self,
        *,
        token_budget: Optional[int] = None,
        recent_count: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        messages = list(self._messages)
        if recent_count is not None:
            messages = messages[-recent_count:]

        budget = token_budget or self.token_window
        if budget <= 0:
            return []

        selected: List[Dict[str, Any]] = []
        running_tokens = 0
        for message in reversed(messages):
            tokens = message.get("metadata", {}).get("tokens", self._estimate_tokens(message.get("content", "")))
            if running_tokens + tokens > budget and selected:
                break
            running_tokens += tokens
            selected.append(message)
        return list(reversed(selected))

    def get_long_term_context(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit is None or limit >= len(self.long_term_context):
            return list(self.long_term_context)
        return list(self.long_term_context[-limit:])

    def get_running_summary(self) -> str:
        return self.running_summary

    def snapshot(self) -> Dict[str, Any]:
        return {
            "messages": copy.deepcopy(self._messages),
            "window_tokens": self._window_tokens,
            "turn_id": self._turn_id,
            "active_turn_id": self._active_turn_id,
            "long_term_context": copy.deepcopy(self.long_term_context),
            "running_summary": self.running_summary,
            "evicted_buffer": copy.deepcopy(self._evicted_turn_buffer),
        }

    def restore(self, snapshot: Dict[str, Any]) -> None:
        self._messages = copy.deepcopy(snapshot.get("messages", []))
        self._window_tokens = snapshot.get("window_tokens", 0)
        self._turn_id = snapshot.get("turn_id", 0)
        self._active_turn_id = snapshot.get("active_turn_id", 0)
        self.long_term_context = copy.deepcopy(snapshot.get("long_term_context", []))
        self.running_summary = snapshot.get("running_summary", "")
        self._evicted_turn_buffer = defaultdict(list, snapshot.get("evicted_buffer", {}))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _append_message(
        self,
        role: str,
        content: str,
        *,
        topics: Optional[Iterable[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        turn_id: Optional[int],
    ) -> None:
        topics_list = list(topics) if topics else []
        tokens = self._estimate_tokens(content)
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

        message = {
            "role": role,
            "content": content,
            "metadata": entry_metadata,
        }

        self._messages.append(message)
        self._window_tokens += tokens
        self._enforce_window()

        if role != "assistant":
            self._refresh_running_summary()

    def _enforce_window(self) -> None:
        if self.token_window <= 0:
            return
        while self._messages and self._window_tokens > self.token_window:
            evicted = self._messages.pop(0)
            tokens = evicted.get("metadata", {}).get("tokens", self._estimate_tokens(evicted.get("content", "")))
            self._window_tokens = max(0, self._window_tokens - tokens)
            self._promote_to_long_term(evicted)

    def _promote_to_long_term(self, message: Dict[str, Any]) -> None:
        metadata = message.get("metadata", {})
        turn_id = metadata.get("turn_id")
        if turn_id is None:
            self._append_long_term_entry([message])
            return

        self._evicted_turn_buffer[turn_id].append(message)
        if not self._is_turn_in_window(turn_id):
            buffered = self._evicted_turn_buffer.pop(turn_id, [])
            if buffered:
                self._append_long_term_entry(buffered)

    def _append_long_term_entry(self, messages: List[Dict[str, Any]]) -> None:
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

            snippet = self._shorten(msg.get("content", ""))
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

        self.long_term_context.append(entry)
        if len(self.long_term_context) > self.max_long_term_entries:
            self.long_term_context = self.long_term_context[-self.max_long_term_entries:]
        self._refresh_running_summary()

    def _is_turn_in_window(self, turn_id: int) -> bool:
        for message in self._messages:
            metadata = message.get("metadata", {})
            if metadata.get("turn_id") == turn_id:
                return True
        return False

    def _refresh_running_summary(self) -> None:
        summary_lines: List[str] = []
        if self.long_term_context:
            summary_lines.append("Long-term context:")
            for entry in self.long_term_context[-3:]:
                turn_span = entry.get("turn_ids") or []
                if turn_span:
                    first = turn_span[0]
                    last = turn_span[-1]
                    turn_label = f"turn {first}" if first == last else f"turns {first}-{last}"
                else:
                    turn_label = "misc"
                summary_lines.append(f"- {turn_label}: {entry.get('summary', '')}")

        recent_messages = self.get_messages(token_budget=self.summary_token_budget)
        if recent_messages:
            summary_lines.append("Recent focus:")
            for msg in recent_messages[-4:]:
                role = msg.get("role")
                snippet = self._shorten(msg.get("content", ""), limit=160)
                turn_id = msg.get("metadata", {}).get("turn_id")
                if turn_id:
                    summary_lines.append(f"- ({role}, turn {turn_id}) {snippet}")
                else:
                    summary_lines.append(f"- ({role}) {snippet}")

        joined = "\n".join(summary_lines).strip()
        if self._estimate_tokens(joined) > self.summary_token_budget:
            # Trim oldest lines until within budget
            pruned: List[str] = []
            running = 0
            for line in summary_lines:
                running += self._estimate_tokens(line)
                if running > self.summary_token_budget:
                    break
                pruned.append(line)
            joined = "\n".join(pruned).strip()

        self.running_summary = joined

    @staticmethod
    def _shorten(text: str, *, limit: int = 120) -> str:
        stripped = text.strip()
        if len(stripped) <= limit:
            return stripped
        return stripped[: limit - 3].rstrip() + "..."
