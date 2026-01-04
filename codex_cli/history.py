

class ConversationHistory:
    def __init__(self, levels=5, chunk_size=10):
        self.levels = levels
        self.chunk_size = chunk_size
        # Each level is a list: level 0 = raw, 1+ = summaries
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
        # Only roll up if this level has 2x chunk_size
        while len(self.memory[level]) > 2 * self.chunk_size:
            # Summarize/categorize the oldest chunk_size messages
            chunk = self.memory[level][:self.chunk_size]
            summary = self._summarize_chunk(chunk, level)
            # Remove summarized messages
            self.memory[level] = self.memory[level][self.chunk_size:]
            # Add summary to next level
            if level + 1 < self.levels:
                self.memory[level + 1].append(summary)
                self._rollup_if_needed(level + 1)

    def _summarize_chunk(self, chunk, level):
        # Placeholder: In real use, call LLM to summarize/categorize
        user_msgs = [m["content"] for m in chunk if m["role"] == "user"]
        assistant_msgs = [m["content"] for m in chunk if m["role"] == "assistant"]
        return {
            "role": f"summary_level_{level+1}",
            "content": f"Summary of {len(chunk)} messages. Users: {user_msgs[:1]}... Assistants: {assistant_msgs[:1]}..."
        }

    def get_messages(self):
        # Return all summaries (oldest to newest), then current raw messages
        result = []
        for lvl in range(self.levels - 1, 0, -1):
            result.extend(self.memory[lvl])
        result.extend(self.memory[0])
        return result[-(self.chunk_size * self.levels):]  # max 50-60 entries
