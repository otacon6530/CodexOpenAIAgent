from .api import OpenAIClient
from .history import ConversationHistory
from .config import load_config

import sys

def main():
    config = load_config()
    client = OpenAIClient(config)
    history = ConversationHistory()
    print("codex-cli (type 'exit' to quit)")
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit"): break
            if not user_input: continue
            history.add_user_message(user_input)
            print("Assistant:", end=" ", flush=True)
            for chunk in client.stream_chat(history.get_messages()):
                print(chunk, end="", flush=True)
            print()
            assistant_reply = client.get_last_response()
            history.add_assistant_message(assistant_reply)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

if __name__ == "__main__":
    main()
