
import copy
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional
from core.functions.default_token_estimator import default_token_estimator
from core.functions.shorten import shorten
from core.functions.make_entry_metadata import make_entry_metadata
from core.functions.promote_to_long_term import promote_to_long_term
from core.functions.append_long_term_entry import append_long_term_entry


class ConversationHistory:
    """Tracks short-term messages with a token-aware window and long-term summaries."""

    def get_efficient_prompt(self, *, include_system=True, recent_turns=3, tool_instructions=None):
        """
        Build an efficient prompt for the LLM:
        - Only include system instructions from persistent history (never tool descriptions)
        - Only include the last N user/assistant turns (default 3)
        - Optionally append tool_instructions as a system message if provided (not stored in history)
        """
        prompt = []
        # Only add system messages that are NOT tool descriptions
        for m in self._messages:
            if m["role"] == "system" and not ("Available tools:" in m["content"]):
                m_no_meta = {k: v for k, v in m.items() if k != "metadata"}
                prompt.append(m_no_meta)
        if tool_instructions:
            prompt.append({"role": "system", "content": tool_instructions})
        # Only include the last N user/assistant turns (excluding system)
        non_system = [m for m in self._messages if m["role"] != "system"]
        for m in non_system[-recent_turns*2:]:
            m_no_meta = {k: v for k, v in m.items() if k != "metadata"}
            prompt.append(m_no_meta)
        return prompt

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
        self._estimate_tokens = token_estimator or default_token_estimator

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
        entry_metadata = make_entry_metadata(content, topics, metadata, turn_id, self._estimate_tokens)
        message = {
            "role": role,
            "content": content,
            "metadata": entry_metadata,
        }
        self._messages.append(message)
        self._window_tokens += entry_metadata["tokens"]
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
            promote_to_long_term(evicted, self._evicted_turn_buffer, self._is_turn_in_window, lambda msgs: append_long_term_entry(msgs, self.long_term_context, self.max_long_term_entries, self._estimate_tokens, self._refresh_running_summary))

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
                snippet = shorten(msg.get("content", ""), limit=160)
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

    # _shorten is now imported

class History:
    def __init__(self, *args, **kwargs):
        self.history = ConversationHistory(*args, **kwargs)

    def get_efficient_prompt(self, *args, **kwargs):
        return self.history.get_efficient_prompt(*args, **kwargs)

    def add_system_message(self, *args, **kwargs):
        return self.history.add_system_message(*args, **kwargs)

    def add_user_message(self, *args, **kwargs):
        return self.history.add_user_message(*args, **kwargs)

    def add_assistant_message(self, *args, **kwargs):
        return self.history.add_assistant_message(*args, **kwargs)

    def get_messages(self, *args, **kwargs):
        return self.history.get_messages(*args, **kwargs)

    def get_long_term_context(self, *args, **kwargs):
        return self.history.get_long_term_context(*args, **kwargs)

    def get_running_summary(self):
        return self.history.get_running_summary()

    def snapshot(self):
        return self.history.snapshot()

    def restore(self, snapshot):
        return self.history.restore(snapshot)
