# codex-cli

A modular command-line interface to interact with your LLM via an OpenAI-compatible API.

## Features
- REPL-style chat with your LLM
- Streaming responses
- Modular codebase (API, history, config, CLI)

## Requirements
- Python 3.8+
- `requests` library (`pip install requests`)

## Setup
1. Clone or copy this repo/folder.
2. Install dependencies:
   ```sh
   pip install requests
   ```
3. Set environment variables (or edit config.py):
   - `OPENAI_API_URL` (default: http://localhost:11434/v1/chat/completions)
   - `OPENAI_API_KEY` (default: sk-xxx)
   - `OPENAI_MODEL` (default: gpt-3.5-turbo)

## Usage
From the project root, run:

```sh
python -m codex_cli.cli
```

Or, if you prefer, run directly:

```sh
python codex_cli/cli.py
```

Type your message and press Enter. Type `exit` or `quit` to leave.

## Customization
- Edit `config.py` or set environment variables to change API endpoint, key, or model.
- Extend modules in `codex_cli/` to add features (history saving, command-line args, etc).

## Example
```
You: Hello!
Assistant: Hi! How can I help you today?
```

---

For issues or improvements, edit the code and re-run as needed.
