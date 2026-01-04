class ConversationHistory:
    def __init__(self, levels=5, chunk_size=10):
        self.levels = levels
        self.chunk_size = chunk_size
        self.memory = [[] for _ in range(levels)]

    def add_system_message(self, content):
        self.memory[0].append({"role": "system", "content": content})
        self._rollup_if_needed(0)

    def add_user_message(self, content):
        self.memory[0].append({"role": "user", "content": content})
        self._rollup_if_needed(0)

    def add_assistant_message(self, content):
        self.memory[0].append({"role": "assistant", "content": content})
        self._rollup_if_needed(0)

    def _rollup_if_needed(self, level):
        while len(self.memory[level]) > 2 * self.chunk_size:
            chunk = self.memory[level][:self.chunk_size]
            summary = self._summarize_chunk(chunk, level)
            self.memory[level] = self.memory[level][self.chunk_size:]
            if level + 1 < self.levels:
                self.memory[level + 1].append(summary)
                self._rollup_if_needed(level + 1)

    def _summarize_chunk(self, chunk, level):
        user_msgs = [m["content"] for m in chunk if m["role"] == "user"]
        assistant_msgs = [m["content"] for m in chunk if m["role"] == "assistant"]
        return {
            "role": f"summary_level_{level + 1}",
            "content": (
                f"Summary of {len(chunk)} messages. "
                f"Users: {user_msgs[:1]}... Assistants: {assistant_msgs[:1]}..."
            ),
        }

    def get_messages(self):
        result = []
        for lvl in range(self.levels - 1, 0, -1):
            result.extend(self.memory[lvl])
        result.extend(self.memory[0])
        return result[-(self.chunk_size * self.levels):]
